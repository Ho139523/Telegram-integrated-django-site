import os  
import time  
import threading  
import subprocess  

# Function to perform git pull  
def git_pull():  
    while True:  
        try:  
            print("Performing git pull...")  
            subprocess.run(["git", "pull", "origin", "master"], check=True)  
            print("Git pull completed.")  
        except subprocess.CalledProcessError as e:  
            print(f"Error during git pull: {e}")  
        time.sleep(5)  # Sleep for 2 minutes  

# Function to install packages from requirements.txt  
def install_requirements():  
    while True:  
        try:  
            print("Installing requirements from requirements.txt...")  
            subprocess.run(["pip", "install", "-r", "requirements-2.txt"], check=True)  
            print("Requirements installed.")  
        except subprocess.CalledProcessError as e:  
            print(f"Error during installation: {e}")  
        time.sleep(3600)  # Sleep for 1 hour  

# Create threads for git pull and install requirements  
pull_thread = threading.Thread(target=git_pull)  
install_thread = threading.Thread(target=install_requirements)  

# Start threads  
pull_thread.start()  
install_thread.start()  

# Optional: join threads if you want to wait for them to finish (they run indefinitely)  
pull_thread.join()  
install_thread.join()