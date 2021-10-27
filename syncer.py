from threading import Timer
import sync_files 

def syncer():
    print("\n\n\n --------- Trying to Sync --------\n\n")
    sync_files.sync_files()
    Timer(20, syncer).start()

syncer()
