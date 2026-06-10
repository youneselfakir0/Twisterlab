import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    from twisterlab.services.system_client import DockerSystemClient
    print("Class imported successfully")
    
    # Try to instantiate
    try:
        client = DockerSystemClient()
        print("Instantiation SUCCESS")
    except TypeError as e:
        print(f"Instantiation FAILED: {e}")
        
    # Inspect abstract methods
    import abc
    abstract_methods = getattr(DockerSystemClient, "__abstractmethods__", set())
    print(f"Abstract methods remaining: {abstract_methods}")

except Exception as e:
    print(f"Import FAILED: {e}")
