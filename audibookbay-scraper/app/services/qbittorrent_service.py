from qbittorrentapi import Client, APIConnectionError, LoginFailed, NotFound404Error, Conflict409Error, Forbidden403Error
from typing import Optional, Dict, Any
import logging
import pathlib # For path manipulation
import re # For sanitizing the title

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QBittorrentService:
    def __init__(self):
        self.client = None
        try:
            self.client = Client(
                host=settings.QBITTORRENT_HOST,
                port=settings.QBITTORRENT_PORT,
                username=settings.QBITTORRENT_USERNAME,
                password=settings.QBITTORRENT_PASSWORD,
                # SIMPLE_RESPONSES=True, # Makes responses easier to work with, less verbose
                # VERIFY_WEBUI_CERTIFICATE=False, # If using self-signed cert for qbit HTTPS
                REQUESTS_ARGS={"timeout": 10} # Set a timeout for requests to qbit
            )
            logger.info(f"Attempting to connect to qBittorrent at {settings.QBITTORRENT_HOST}:{settings.QBITTORRENT_PORT}")
            self.client.auth_log_in()
            # Check client version (optional, good for debugging)
            # ver = self.client.app_version()
            # logger.info(f"Successfully connected to qBittorrent version: {ver}")
            web_ui_version = self.client.app_web_api_version()
            logger.info(f"Successfully connected to qBittorrent. WebUI API version: {web_ui_version}")

        except LoginFailed as e:
            logger.error(f"qBittorrent login failed. Please check credentials. Error: {e}")
            self.client = None # Ensure client is None if connection failed
        except APIConnectionError as e:
            logger.error(f"Failed to connect to qBittorrent at {settings.QBITTORRENT_HOST}:{settings.QBITTORRENT_PORT}. Error: {e}")
            self.client = None
        except Exception as e:
            logger.error(f"An unexpected error occurred during qBittorrent client initialization: {e}", exc_info=True)
            self.client = None

    def is_client_available(self) -> bool:
        """Checks if the qBittorrent client is initialized and available."""
        if not self.client:
            logger.warning("qBittorrent client is not available. Connection may have failed during init.")
            return False
        try:
            self.client.app_version() # A simple call to check if the client is responsive
            return True
        except APIConnectionError:
            logger.warning("qBittorrent client seems to be unresponsive.")
            return False
        except Exception as e:
            logger.error(f"Error checking qBittorrent client availability: {e}", exc_info=True)
            return False

    def add_torrent_magnet(self, magnet_link: str, audiobook_title: str) -> Dict[str, Any]:
        """
        Adds a torrent to qBittorrent using a magnet link.

        Args:
            magnet_link: The magnet link for the torrent.
            audiobook_title: The title of the audiobook, used for generating the save path.

        Returns:
            A dictionary with status and message. e.g.:
            {'status': 'success', 'message': 'Torrent added successfully.'}
            {'status': 'error', 'message': 'Error details...'}
        """
        if not self.is_client_available():
            return {"status": "error", "message": "qBittorrent client not available."}

        try:
            # Sanitize audiobook_title to create a valid directory name
            # Replace invalid path characters. This might need to be more robust.
            safe_title = re.sub(r'[\\/*?"<>|:]', '_', audiobook_title)
            # Construct save path: base_path / sanitized_title
            # pathlib.Path handles joining paths correctly for the OS.
            save_path = str(pathlib.Path(settings.QBITTORRENT_SAVE_PATH_BASE) / safe_title)
            
            logger.info(f"Attempting to add magnet: {magnet_link}")
            logger.info(f"Save path: {save_path}")
            logger.info(f"Category: {settings.QBITTORRENT_CATEGORY}")

            result = self.client.torrents_add(
                urls=magnet_link,
                save_path=save_path,
                category=settings.QBITTORRENT_CATEGORY,
                is_paused=False, # Start download immediately
                # use_auto_torrent_management=False, # Let our save_path take precedence if needed
            )
            
            if result == "Ok.": # qbittorrent-api often returns "Ok." on success
                logger.info(f"Torrent '{safe_title}' added successfully to qBittorrent.")
                return {"status": "success", "message": f"Torrent '{safe_title}' added successfully."}
            else:
                # Sometimes result might contain an error message or be empty on failure
                logger.error(f"Failed to add torrent to qBittorrent. Result: '{result}'")
                return {"status": "error", "message": f"Failed to add torrent. qBittorrent responded: '{result}'"}

        except Conflict409Error:
            logger.warning(f"Torrent (magnet: {magnet_link}) already exists in qBittorrent.")
            return {"status": "warning", "message": "Torrent already exists in qBittorrent."}
        except Forbidden403Error as e:
            logger.error(f"qBittorrent returned Forbidden (403). Check IP whitelist or other qBittorrent security settings. Error: {e}")
            return {"status": "error", "message": f"qBittorrent Forbidden: {e}"}
        except NotFound404Error as e: # Should not happen for torrents_add, but good to have
            logger.error(f"qBittorrent API endpoint not found (404). Error: {e}")
            return {"status": "error", "message": f"qBittorrent API endpoint not found: {e}"}
        except APIConnectionError as e:
            logger.error(f"qBittorrent API connection error: {e}")
            return {"status": "error", "message": f"qBittorrent connection error: {e}"}
        except Exception as e:
            logger.error(f"An unexpected error occurred while adding torrent: {e}", exc_info=True)
            return {"status": "error", "message": f"An unexpected error occurred: {e}"}

# Singleton instance (or you can manage instantiation within FastAPI dependencies)
qbt_service = QBittorrentService()

# Example Usage (for direct testing)
if __name__ == "__main__":
    # Ensure your .env file is in the backend directory and has QBITTORRENT_* settings
    # and that your qBittorrent client is running and accessible.
    
    logger.info("--- Testing qBittorrent Service ---")
    if qbt_service.is_client_available():
        logger.info("qBittorrent client is available. Proceeding with test.")
        
        # Find a real magnet link for testing. 
        # WARNING: This will actually download if successful!
        # Example magnet (replace with a small, safe test torrent if you run this):
        # test_magnet = "magnet:?xt=urn:btih:KEYZONG4CL766MET6EZIERBPAVCRV5Y7&dn=Ubuntu%2022.04.3%20LTS%20Desktop%20(64-bit)"
        # test_title = "Ubuntu Test Download"

        # Pull a magnet link from a previous scraper test if possible, or use a known safe one.
        # For this example, let's assume we have one:
        test_magnet_hp = "magnet:?xt=urn:btih:a850ef0cd4f87cb030ba91ebe36b5479733e622c&dn=Empire+of+Salt+Trilogy+%5B1-3%5D&tr=http%3A%2F%2Ftracker2.dler.org%3A80%2Fannounce&tr=http%3A%2F%2Ftracker2.dler.org%3A80%2Fannounce&tr=http%3A%2F%2Ftracker.bt4g.com%3A2095%2Fannounce&tr=http%3A%2F%2Fbt.okmp3.ru%3A2710%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Fp4p.arenabg.com%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.dler.org%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.tiny-vps.com%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce"
        test_title_hp = "Empire of Salt Trilogy Test Download"

        logger.info(f"Attempting to add: {test_title_hp}")
        result = qbt_service.add_torrent_magnet(test_magnet_hp, test_title_hp)
        logger.info(f"Add torrent result: {result}")

        # Example of a magnet that might already exist to test Conflict409Error
        # logger.info(f"Attempting to re-add: {test_title_hp}")
        # result_conflict = qbt_service.add_torrent_magnet(test_magnet_hp, test_title_hp)
        # logger.info(f"Re-add torrent result: {result_conflict}")

    else:
        logger.error("qBittorrent client is NOT available. Please check settings and ensure qBittorrent is running.")
    logger.info("--- qBittorrent Service Test Finished ---") 