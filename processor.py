import os
import json
import time
import threading
from typing import Callable, Optional
from crypto_utils import generate_all_addresses
from api_client import BlockchainAPI

API_DELAY = 1.5  # Delay between API requests in seconds


class FileProcessor:
    def __init__(self, update_callback: Optional[Callable] = None, log_callback: Optional[Callable] = None):
        self.update_callback = update_callback
        self.log_callback = log_callback
        self._stop_event = threading.Event()
        self.api = BlockchainAPI(log_callback=log_callback)

    @property
    def is_running(self) -> bool:
        return not self._stop_event.is_set()

    def log(self, message: str):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def process_file(self, filepath: str, mode: str = "all", start_line: int = 1):
        self._stop_event.clear()

        # Create output directories
        base_dir = os.path.dirname(filepath)
        with_txs_dir = os.path.join(base_dir, "with_txs")
        no_txs_dir = os.path.join(base_dir, "no_txs")
        with_balance_dir = os.path.join(base_dir, "with_balance")

        os.makedirs(with_txs_dir, exist_ok=True)
        os.makedirs(no_txs_dir, exist_ok=True)
        os.makedirs(with_balance_dir, exist_ok=True)

        try:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip()]
            except UnicodeDecodeError:
                with open(filepath, 'r', encoding='cp1251', errors='ignore') as f:
                    lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.log(f"Ошибка чтения файла: {e}")
            return

        total_lines = len(lines)
        self.log(f"Найдено строк для обработки: {total_lines}")

        start_index = max(0, start_line - 1)
        if start_index >= total_lines:
            self.log("Начальная строка превышает количество строк в файле.")
            return

        if start_index > 0:
            self.log(f"Пропуск первых {start_index} строк. Начинаем со строки {start_line}.")

        stopped = False
        for i in range(start_index, total_lines):
            if not self.is_running:
                self.log("Процесс остановлен пользователем.")
                stopped = True
                break

            line = lines[i]
            self.log(f"Обработка [{i+1}/{total_lines}]: {line}")

            # Generate addresses
            data = generate_all_addresses(line)

            # Addresses to check
            addresses = [
                data["p2pkh_compressed"],
                data["p2pkh_uncompressed"],
                data["p2sh_p2wpkh_compressed"],
                data["p2wpkh_compressed"]
            ]

            total_txs = 0
            total_balance = 0
            address_stats = {}

            for addr in addresses:
                if not self.is_running:
                    stopped = True
                    break

                time.sleep(API_DELAY)

                info = self.api.get_address_info(addr)
                address_stats[addr] = info

                total_txs += info['tx_count']
                total_balance += info['balance']

                if mode in ("all", "txs") and info['tx_count'] > 0:
                    self.log(f"  -> {addr}: {info['tx_count']} txs")
                if mode in ("all", "balance") and info['balance'] > 0:
                    self.log(f"  -> {addr}: {info['balance']} sats")

            if stopped:
                self.log("Процесс остановлен пользователем.")
                break

            data["stats"] = address_stats
            data["total_txs"] = total_txs
            data["total_balance"] = total_balance

            # Save to JSON
            filename = f"{data['p2pkh_compressed']}.json"

            save_path = None
            if mode == "balance":
                if total_balance > 0:
                    save_path = os.path.join(with_balance_dir, filename)
            elif mode == "txs":
                if total_txs > 0:
                    save_path = os.path.join(with_txs_dir, filename)
                else:
                    save_path = os.path.join(no_txs_dir, filename)
            elif mode == "all":
                if total_balance > 0:
                    save_path = os.path.join(with_balance_dir, filename)
                elif total_txs > 0:
                    save_path = os.path.join(with_txs_dir, filename)
                else:
                    save_path = os.path.join(no_txs_dir, filename)

            if save_path:
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)

            if self.update_callback:
                self.update_callback(i + 1, total_lines)

        if not stopped:
            self.log("Обработка завершена.")

        if self.update_callback:
            self.update_callback(total_lines, total_lines)

    def stop(self):
        self._stop_event.set()
