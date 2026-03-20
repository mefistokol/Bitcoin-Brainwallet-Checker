import requests
import time


class BlockchainAPI:
    def __init__(self, log_callback=None):
        self.base_url = "https://mempool.space/api"
        self.session = requests.Session()
        self.log_callback = log_callback

    def log(self, message: str):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def get_address_info(self, address: str, retries: int = 3) -> dict:
        """
        Fetches balance and transaction count for a given Bitcoin address.
        Returns a dict: {'balance': int, 'tx_count': int}
        """
        url = f"{self.base_url}/address/{address}"

        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    chain_stats = data.get('chain_stats', {})
                    mempool_stats = data.get('mempool_stats', {})

                    # Calculate balance (funded - spent)
                    funded = chain_stats.get('funded_txo_sum', 0) + mempool_stats.get('funded_txo_sum', 0)
                    spent = chain_stats.get('spent_txo_sum', 0) + mempool_stats.get('spent_txo_sum', 0)
                    balance = funded - spent

                    tx_count = chain_stats.get('tx_count', 0) + mempool_stats.get('tx_count', 0)

                    return {
                        'balance': balance,
                        'tx_count': tx_count
                    }
                elif response.status_code == 429:
                    # Rate limited
                    self.log(f"Rate limited for {address}, retrying in {2 ** attempt}s...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    self.log(f"Error fetching {address}: HTTP {response.status_code}")
                    time.sleep(1)

            except requests.RequestException as e:
                self.log(f"Request failed for {address}: {e}")
                time.sleep(2)

        # If all retries fail, return 0
        return {'balance': 0, 'tx_count': 0}
