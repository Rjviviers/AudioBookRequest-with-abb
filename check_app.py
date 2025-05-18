"""
Script to check if we can import the main app.
"""
import sys
import os

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Attempting to import app.main...")
    import app.main
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
    
    # Try to see what modules are available
    print("\nChecking app directory...")
    try:
        import app
        print("Successfully imported app module")
        
        # Check for services module
        print("\nChecking for services module...")
        try:
            if not os.path.exists("app/services"):
                print("app/services directory does not exist!")
                os.makedirs("app/services", exist_ok=True)
                print("Created app/services directory")
            
            if not os.path.exists("app/services/__init__.py"):
                print("app/services/__init__.py does not exist!")
                with open("app/services/__init__.py", "w") as f:
                    f.write('"""Services module."""\n')
                print("Created app/services/__init__.py")
            
            # Verify scraper service
            if not os.path.exists("app/services/scraper_service.py"):
                print("app/services/scraper_service.py does not exist!")
            else:
                print("app/services/scraper_service.py exists")
            
            # Try to import the services module
            import app.services
            print("Successfully imported app.services module")
            
            # Try to import the scraper_service module
            try:
                import app.services.scraper_service
                print("Successfully imported app.services.scraper_service module")
            except Exception as e:
                print(f"Failed to import app.services.scraper_service: {e}")
                
        except Exception as e:
            print(f"Error checking services: {e}")
            
        # Check for the audiobookbay router
        print("\nChecking for audiobookbay router...")
        if not os.path.exists("app/routers/audiobookbay.py"):
            print("app/routers/audiobookbay.py does not exist!")
        else:
            print("app/routers/audiobookbay.py exists")
            
        # Try to import the routers module
        try:
            import app.routers
            print("Successfully imported app.routers module")
            
            # Try to import the audiobookbay module
            try:
                import app.routers.audiobookbay
                print("Successfully imported app.routers.audiobookbay module")
            except Exception as e:
                print(f"Failed to import app.routers.audiobookbay: {e}")
        except Exception as e:
            print(f"Failed to import app.routers: {e}")
            
    except Exception as e:
        print(f"Failed to import app module: {e}") 