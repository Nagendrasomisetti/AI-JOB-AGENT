import time
import logging
import threading
import argparse
from main import run_agent

# Configure scheduler logging
logger = logging.getLogger("AIJobAgent.Scheduler")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class IngestionScheduler:
    """
    Background scheduler daemon that orchestrates central job ingestion pipelines in periodic loops.
    Uses threading.Event for responsive, interruptible sleeps.
    """
    def __init__(self, interval_seconds: int = 86400, query: str = "Find ML and AI jobs"):
        """
        Args:
            interval_seconds (int): Ingestion loop cycle interval (Default: 86400 seconds = 24 hours).
            query (str): The search query to ingest.
        """
        self.interval = interval_seconds
        self.query = query
        self.stop_event = threading.Event()
        self.thread = None
        self.running = False

    def start(self) -> None:
        """
        Launches the periodic ingestion pipeline in a decoupled background thread.
        """
        if self.running:
            logger.warning("Scheduler is already active.")
            return

        self.running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Background Ingestion Scheduler activated. Loop cycle: {self.interval}s (~{self.interval/3600:.1f}h).")

    def stop(self) -> None:
        """
        Signals the background thread to safely wind down and exit.
        """
        if not self.running:
            return

        logger.info("Signaling background ingestion thread to shutdown...")
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=10)
            logger.info("Background Ingestion Scheduler successfully deactivated.")

    def _run_loop(self) -> None:
        """
        The internal loop execution cycle running inside the background thread.
        """
        logger.info("Scheduler thread launched. Executing initial cold ingestion sweep...")
        
        while not self.stop_event.is_set():
            try:
                # 1. Trigger the central ETL agent run
                new_jobs = run_agent(query=self.query, limit_per_source=5)
                logger.info(f"[Ingestion Log] Ingest sweep completed. Discovered {len(new_jobs)} brand new listings.")
            except Exception as e:
                logger.error(f"[Ingestion Error] Central pipeline execution failed: {e}")
            
            # 2. Compute next execution date for logging
            next_run = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + self.interval))
            logger.info(f"Sleeping for {self.interval} seconds. Next background sweep scheduled at: {next_run}")
            
            # 3. Sleep interruptibly via threading.Event
            # If stop_event is set during this sleep, it immediately returns True, breaking the loop!
            interrupted = self.stop_event.wait(timeout=self.interval)
            if interrupted:
                logger.info("Scheduler thread interrupted via shutdown signal.")
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous Job Platform Background Ingestion Scheduler")
    parser.add_argument(
        "--interval", 
        type=int, 
        default=86400, 
        help="Crawl loop interval time in seconds (Default: 86400 = 24 hours)"
    )
    parser.add_argument(
        "--query", 
        type=str, 
        default="Find ML and AI jobs", 
        help="Search query terms for collectors (Default: 'Find ML and AI jobs')"
    )
    
    args = parser.parse_args()

    print("=" * 60)
    print("[AGENT] AI JOB AGENT - INGESTION DAEMON SERVER")
    print("=" * 60)
    
    scheduler = IngestionScheduler(interval_seconds=args.interval, query=args.query)
    
    try:
        scheduler.start()
        # Keep the primary shell process active
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("\nShutting down ingestion daemon server gracefully...")
        scheduler.stop()
        print("Goodbye!")
