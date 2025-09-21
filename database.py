import os
import logging
import certifi
from dotenv import load_dotenv
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

user_collection = None

# Initialize database connection
async def init_db():
    """Initialize MongoDB connection for user collection."""
    global user_collection
    try:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            logger.error("MONGO_URI not set in .env")
            raise ValueError("MONGO_URI environment variable is not set")
        
        # Initialize MongoDB client
        client = AsyncIOMotorClient(
            mongo_uri,
            tls=True,
            tlsCAFile=certifi.where(),
            # tlsAllowInvalidCertificates=True,  # Uncomment for debugging only
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        # Test connection with detailed error logging
        try:
            await client.admin.command("ping")
            logger.info("Connection to MongoDB established")
        except Exception as ping_error:
            logger.error(f"Failed to ping MongoDB: {str(ping_error)}")
            raise
        
        database = client.website_chat
        user_collection = database.get_collection("user_collection")
        return user_collection
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {str(e)}")
        raise

# Helper to convert MongoDB user object to dictionary
def user_helper(user) -> dict:
    """Convert MongoDB user document to dictionary, excluding password."""
    return {
        "id": str(user["_id"]),
        "email": user["email"]
    }

# Add a new user
async def add_user(user_data: dict) -> dict:
    """Add a new user to the database."""
    try:
        user = await user_collection.insert_one(user_data)
        new_user = await user_collection.find_one({"_id": user.inserted_id})
        logger.info(f"Added user: {new_user['email']}")
        return user_helper(new_user)
    except Exception as e:
        logger.error(f"Error adding user: {str(e)}")
        raise

# Get a user by email
async def get_user_by_email(email: str) -> dict:
    """Retrieve a user by email."""
    try:
        user = await user_collection.find_one({"email": email})
        if user:
            logger.info(f"Retrieved user: {email}")
            return user  # Return full document including hashed_password
        logger.warning(f"User not found: {email}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving user by email: {str(e)}")
        raise

# Get a user by ID
async def get_user(id: str) -> dict:
    """Retrieve a user by ID."""
    try:
        user = await user_collection.find_one({"_id": ObjectId(id)})
        if user:
            logger.info(f"Retrieved user by ID: {id}")
            return user_helper(user)
        logger.warning(f"User not found by ID: {id}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving user by ID: {str(e)}")
        raise

# Update a user by ID
async def update_user(id: str, user_data: dict) -> dict:
    """Update a user by ID."""
    try:
        updated_user = await user_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": user_data},
            return_document=True
        )
        if updated_user:
            logger.info(f"Updated user: {id}")
            return user_helper(updated_user)
        logger.warning(f"User not found for update: {id}")
        return None
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise

# Delete a user by ID
async def delete_user(id: str) -> dict:
    """Delete a user by ID."""
    try:
        deleted_user = await user_collection.find_one_and_delete({"_id": ObjectId(id)})
        if deleted_user:
            logger.info(f"Deleted user: {id}")
            return user_helper(deleted_user)
        logger.warning(f"User not found for deletion: {id}")
        return None
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise