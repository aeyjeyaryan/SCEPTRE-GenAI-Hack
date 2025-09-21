import os
import logging
import asyncio
from typing import List, Dict, Any
import google.generativeai as genai
from search_utils import search_documents, SearchResults
import re

# Configure logging
logger = logging.getLogger(__name__)

class FactChecker:
    """Handles fact-checking and verification of claims against trusted sources."""
    
    def __init__(self):
        # Configure Gemini
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("Missing GEMINI_API_KEY environment variable")
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Trusted domains for fact-checking
        self.trusted_domains = {
            '.gov', '.edu', '.org',
            'reuters.com', 'apnews.com', 'bbc.com', 'npr.org',
            'factcheck.org', 'snopes.com', 'politifact.com',
            'who.int', 'cdc.gov', 'nih.gov', 'nasa.gov'
        }
    
    async def verify_claims(self, content: str) -> Dict[str, Any]:
        """
        Verify claims in content against trusted sources.
        Returns verification score and evidence sources.
        """
        try:
            # Step 1: Extract key claims from content
            claims = await self._extract_claims(content)
            
            if not claims:
                return {
                    "score": 0.5,  # Neutral score when no claims found
                    "sources": [],
                    "details": "No verifiable claims found in content."
                }
            
            # Step 2: Search for evidence for each claim
            all_sources = []
            claim_scores = []
            
            for claim in claims:
                try:
                    # Search for information about this claim
                    search_query = self._create_search_query(claim)
                    search_results = await search_documents(search_query)
                    
                    if search_results.status == "success" and search_results.results:
                        # Filter for trusted sources
                        trusted_results = self._filter_trusted_sources(search_results.results)
                        
                        if trusted_results:
                            # Verify claim against found sources
                            claim_score = await self._verify_single_claim(claim, trusted_results)
                            claim_scores.append(claim_score)
                            
                            # Add sources to overall list
                            for result in trusted_results[:3]:  # Top 3 sources per claim
                                all_sources.append({
                                    "title": result.title,
                                    "url": result.url,
                                    "snippet": result.snippet,
                                    "claim": claim,
                                    "relevance_score": result.relevance_score
                                })
                        else:
                            # No trusted sources found for this claim
                            claim_scores.append(0.2)  # Low score for unverifiable claims
                    else:
                        # No search results found
                        claim_scores.append(0.3)  # Slightly higher than completely unverifiable
                        
                except Exception as e:
                    logger.error(f"Error verifying claim '{claim}': {e}")
                    claim_scores.append(0.3)  # Default low score for errors
            
            # Step 3: Calculate overall verification score
            if claim_scores:
                overall_score = sum(claim_scores) / len(claim_scores)
            else:
                overall_score = 0.3  # Default when no claims could be verified
            
            # Remove duplicates from sources
            unique_sources = self._deduplicate_sources(all_sources)
            
            return {
                "score": min(max(overall_score, 0.0), 1.0),  # Clamp between 0 and 1
                "sources": unique_sources[:10],  # Limit to top 10 sources
                "details": f"Analyzed {len(claims)} claims against {len(unique_sources)} trusted sources."
            }
            
        except Exception as e:
            logger.error(f"Error in fact verification: {e}")
            return {
                "score": 0.3,  # Default low score for errors
                "sources": [],
                "details": f"Error during verification: {str(e)}"
            }
    
    async def _extract_claims(self, content: str) -> List[str]:
        """Extract verifiable claims from content using Gemini."""
        try:
            prompt = f"""
            Analyze the following content and extract specific, factual claims that can be verified.
            Focus on:
            1. Statements of fact (statistics, dates, events)
            2. Claims about people, organizations, or entities
            3. Assertions about scientific, medical, or technical information
            4. Any controversial or disputed statements
            
            Return ONLY the claims, one per line, without explanations or commentary.
            If no verifiable claims are found, return "NO_CLAIMS".
            
            Content to analyze:
            {content}
            """
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            if response and response.text:
                text = response.text.strip()
                if text == "NO_CLAIMS":
                    return []
                
                # Split into individual claims and clean up
                claims = [claim.strip() for claim in text.split('\n') if claim.strip()]
                # Remove numbering and bullet points
                cleaned_claims = []
                for claim in claims:
                    cleaned = re.sub(r'^\d+\.?\s*', '', claim)  # Remove numbering
                    cleaned = re.sub(r'^[-*•]\s*', '', cleaned)  # Remove bullet points
                    if len(cleaned) > 10:  # Only keep substantial claims
                        cleaned_claims.append(cleaned)
                
                return cleaned_claims[:5]  # Limit to 5 claims for efficiency
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting claims: {e}")
            return []
    
    def _create_search_query(self, claim: str) -> str:
        """Create an effective search query for a claim."""
        # Remove common phrases and focus on key terms
        query = claim.lower()
        
        # Remove common prefixes
        prefixes_to_remove = [
            'according to', 'studies show', 'research indicates',
            'it is claimed that', 'reports suggest', 'allegedly'
        ]
        
        for prefix in prefixes_to_remove:
            query = query.replace(prefix, '')
        
        # Extract key terms (nouns, proper nouns, numbers)
        words = query.split()
        key_words = []
        
        for word in words:
            # Keep important words
            if (len(word) > 3 and 
                not word in ['that', 'this', 'these', 'those', 'they', 'them', 'their'] and
                not word.startswith(('a ', 'an ', 'the '))):
                key_words.append(word)
        
        # Limit query length
        search_query = ' '.join(key_words[:8])
        return search_query.strip()
    
    def _filter_trusted_sources(self, search_results) -> List:
        """Filter search results to include only trusted sources."""
        trusted_results = []
        
        for result in search_results:
            url_lower = result.url.lower()
            is_trusted = any(domain in url_lower for domain in self.trusted_domains)
            
            # Additional trust indicators
            if not is_trusted:
                # Check for other indicators of trustworthiness
                trust_indicators = [
                    'university', 'journal', 'academic', 'research',
                    'government', 'official', 'institute'
                ]
                if any(indicator in url_lower or indicator in result.title.lower() 
                       for indicator in trust_indicators):
                    is_trusted = True
            
            if is_trusted:
                trusted_results.append(result)
        
        # Sort by relevance score
        return sorted(trusted_results, key=lambda x: x.relevance_score, reverse=True)
    
    async def _verify_single_claim(self, claim: str, trusted_sources: List) -> float:
        """Verify a single claim against trusted sources."""
        try:
            # Prepare evidence from sources
            evidence = []
            for source in trusted_sources[:5]:  # Use top 5 sources
                evidence.append(f"Source: {source.title}\nContent: {source.content[:500]}...")
            
            evidence_text = "\n\n".join(evidence)
            
            prompt = f"""
            Evaluate the following claim against the provided evidence from trusted sources.
            
            Claim to verify: "{claim}"
            
            Evidence from trusted sources:
            {evidence_text}
            
            Based on the evidence, rate the claim's accuracy on a scale of 0.0 to 1.0 where:
            - 1.0 = Completely true and well-supported by evidence
            - 0.8 = Mostly true with minor inaccuracies
            - 0.6 = Partially true but missing context or oversimplified
            - 0.4 = Mixed evidence, some truth but significant issues
            - 0.2 = Mostly false or misleading
            - 0.0 = Completely false or no supporting evidence
            
            Respond with ONLY a number between 0.0 and 1.0, followed by a brief explanation.
            Format: "SCORE: X.X - Brief explanation"
            """
            
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            if response and response.text:
                text = response.text.strip()
                # Extract score
                if "SCORE:" in text:
                    score_part = text.split("SCORE:")[1].split("-")[0].strip()
                    try:
                        score = float(score_part)
                        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
                    except ValueError:
                        pass
            
            # Default score if parsing fails
            return 0.5
            
        except Exception as e:
            logger.error(f"Error verifying claim: {e}")
            return 0.3
    
    def _deduplicate_sources(self, sources: List[Dict]) -> List[Dict]:
        """Remove duplicate sources based on URL."""
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            url = source.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        
        # Sort by relevance score
        return sorted(unique_sources, key=lambda x: x.get("relevance_score", 0), reverse=True)