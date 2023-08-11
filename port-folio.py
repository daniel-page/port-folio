"""

Port-Folio

A command line application for tracking investments.

"""

# TODO:
# Strip whitespace on text entry, if nothing is entered
# Add dates to holdings
# Add cost basis
# List order
# Stocks splits etc
# Add different investment types
# Add docstrings and better names for variables
# Comment SQL code
# Multiple databases
# SQL aliases?

import sqlite3 as sqlite
import os
from tabulate import tabulate
import logging

logging.basicConfig(
    filename="app.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)


class Portfolio:
    """Functions for the Port-Folio command line application."""

    def __init__(self):
        self.db = sqlite.connect("data.db")
        self.create_positions_sql_table()
        self.create_prices_sql_table()

    def create_positions_sql_table(self):
        """Create an SQLite table for positions if it does not already exist."""

        self.db.execute(
            """
                CREATE TABLE IF NOT EXISTS POSITIONS (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    holding TEXT,
                    quantity FLOAT,
                    buy_price FLOAT
                );
            """
        )

    def create_prices_sql_table(self):
        """Create an SQLite table for prices if it does not already exist."""

        self.db.execute(
            """
                CREATE TABLE IF NOT EXISTS PRICES (
                    holding TEXT,
                    current_price FLOAT
                );
            """
        )

    def create_position(self, holding, quantity, price):
        """Create an entry in the positions table based on user inputs."""

        self.db.execute(
            f"""
                INSERT INTO POSITIONS (holding, quantity, buy_price) 
                    VALUES ('{holding}', {quantity:.2f}, {price:.2f});
            """
        )

        self.db.commit()

    def remove_position(self, level_2_option, level_3_option):
        """Remove a holding position entry."""

        # Removes a transaction from the POSITIONS table based on an index
        self.db.execute(
            f"""
                DELETE FROM POSITIONS WHERE id = (
                SELECT id FROM (
                SELECT id from POSITIONS WHERE holding = (
                SELECT holding FROM POSITIONS GROUP BY holding LIMIT 1 OFFSET {int(level_2_option)-1}))
                LIMIT 1 OFFSET {int(level_3_option)-1});
            """
        )

        # If there is a holding entry in the PRICES table that is not in the
        # POSITIONS table then it will be deleted
        self.db.execute(
            "DELETE FROM PRICES WHERE holding NOT IN (SELECT holding FROM POSITIONS);"
        )
        self.db.commit()

    def remove_all_positions(self, level_2_option):
        """Delete all positions for a holding."""

        # Removes a transaction from the POSITIONS table based on an index
        self.db.execute(
            f"""
                DELETE FROM POSITIONS WHERE holding = (
                SELECT holding FROM POSITIONS GROUP BY holding LIMIT 1 OFFSET {int(level_2_option)-1});
            """
        )

        # If there is a holding entry in the PRICES table that is not in the
        # POSITIONS table then it will be deleted
        self.db.execute(
            "DELETE FROM PRICES WHERE holding NOT IN (SELECT holding FROM POSITIONS);"
        )

        self.db.commit()

    def create_current_price(self, holding, current_price):
        """Create a price entry."""

        data = self.db.execute(
            f"""SELECT holding FROM PRICES WHERE holding = '{holding}'"""
        ).fetchone()

        if data:
            self.db.execute(
                f"UPDATE PRICES SET current_price = {current_price:.2f} WHERE holding = '{holding}'"
            )
        else:
            self.db.execute(
                f"INSERT INTO PRICES (holding, current_price) VALUES ('{holding}', {current_price:.2f})"
            )

        self.db.commit()

    def update_position_quantity(self, level_2_option, level_3_option, quantity):
        """Updates the quantity of a selected position."""

        self.db.execute(
            f"""
                UPDATE POSITIONS SET quantity = {quantity:.2f} WHERE id = (
                SELECT id FROM (
                SELECT id from POSITIONS WHERE holding = (
                SELECT holding FROM POSITIONS GROUP BY holding LIMIT 1 OFFSET {int(level_2_option)-1}))
                LIMIT 1 OFFSET {int(level_3_option)-1});
            """
        )

        self.db.commit()

    def update_position_buy_price(self, level_2_option, level_3_option, buy_price):
        """Updates the buy price of a selected position."""
        self.db.execute(
            f"""
                UPDATE POSITIONS SET buy_price = {buy_price:.2f} WHERE id = (
                SELECT id FROM (
                SELECT id from POSITIONS WHERE holding = (
                SELECT holding FROM POSITIONS GROUP BY holding LIMIT 1 OFFSET {int(level_2_option)-1}))
                LIMIT 1 OFFSET {int(level_3_option)-1});
            """
        )

        self.db.commit()

    def update_holding_price(self, level_2_option, current_price):
        """Update the price of a holding position."""

        self.db.execute(
            f"""
                UPDATE PRICES SET current_price = {current_price:.2f} WHERE
                holding = (SELECT holding FROM POSITIONS GROUP BY holding LIMIT 1 OFFSET {int(level_2_option)-1});
            """
        )

        self.db.commit()

    def create_overview_as_table(self, sql_data):
        """Generates a table summarising all holdings in the database."""

        formatted_data = []
        counter = 1
        for item in sql_data:
            identifier = f"[{str(counter)}]"
            holding = item[0]

            quantity = f"{item[1]:.2f}".rjust(8)
            current_price = "$" + f"{item[2]:.2f}".rjust(8)
            value = "$" + f"{item[3]:.2f}".rjust(8)
            _return = f"{item[4]:.2f}%".rjust(8)
            row = (identifier, holding, quantity, current_price, value, _return)
            formatted_data.append(row)
            counter += 1

        return formatted_data

    def clear_terminal(self):
        """Clears the terminal of text."""
        os.system("cls||clear")

    def print_overview_table(self):
        """Print an overview of holdings."""

        col_names = [
            "ID",
            "Holding",
            "Quantity",
            "Current\nPrice",
            "Current\nValue",
            "Return",
        ]

        # Can aliases be used here to simplify?
        holdings_groups = self.db.execute(
            """
                SELECT 
                POSITIONS.holding,
                SUM(POSITIONS.quantity),
                PRICES.current_price,
                PRICES.current_price*SUM(POSITIONS.quantity),
                (SUM(POSITIONS.quantity*PRICES.current_price) - SUM(POSITIONS.quantity*POSITIONS.buy_price))/SUM(POSITIONS.quantity*POSITIONS.buy_price)*100 
                FROM PRICES
                LEFT JOIN POSITIONS ON PRICES.holding = POSITIONS.holding
                GROUP by POSITIONS.holding
            """
        ).fetchall()

        # What if price not there
        if len(holdings_groups) != 0:
            table = self.create_overview_as_table(holdings_groups)

            print()
            print(
                tabulate(
                    table,
                    headers=col_names,
                    disable_numparse=True,
                    stralign="right",
                )
            )
            print()

        data = self.db.execute(
            """
                SELECT 
                SUM(PRICES.current_price*POSITIONS.quantity)
                FROM PRICES
                LEFT JOIN POSITIONS ON PRICES.holding = POSITIONS.holding
            """
        ).fetchone()[0]

        if data is not None:
            print(f"Total: ${data:.2f}")

        print()

    def create_single_holding_overview(self, sql_data):
        """Create a table for a single holding."""

        formatted_data = []
        counter = 1
        for item in sql_data:
            identifier = f"[{str(counter)}]"
            quantity = f"{item[0]:.2f}".rjust(8)
            buy_price = "$" + f"{item[1]:.2f}".rjust(8)
            value = "$" + f"{item[2]:.2f}".rjust(8)
            row = (identifier, quantity, buy_price, value)
            formatted_data.append(row)
            counter += 1

        return formatted_data

    def print_single_holding_overview(self, level_1_option):
        """Print a table for a single holding."""

        data = self.db.execute(
            f"""
            SELECT quantity, buy_price, quantity*buy_price FROM POSITIONS WHERE holding = (
            SELECT holding FROM POSITIONS GROUP BY holding LIMIT 1 OFFSET {int(level_1_option)-1});
            """
        )

        table = self.create_single_holding_overview(data)

        col_names = ["ID", "Quantity", "Buy Price", "Buy Value"]

        print()

        print(
            tabulate(
                table,
                headers=col_names,
                disable_numparse=True,
                stralign="right",
            )
        )

        data = self.db.execute(
            f"""
            SELECT holding FROM POSITIONS GROUP BY holding LIMIT 1 OFFSET {int(level_1_option)-1};
            """
        ).fetchone()[0]
        print()

        print(f"Holding: {data}")

        data = self.db.execute(
            f"""
            SELECT current_price FROM PRICES WHERE holding = (SELECT holding FROM POSITIONS GROUP BY holding LIMIT 1 OFFSET {int(level_1_option)-1})
            """
        ).fetchone()[0]

        print(f"Current Price: $ {data:.2f}")

    def print_banner(self):
        """Print program name and logo in ASCII"""
        line_1 = "                    |    |    |                        "
        line_2 = "                   )_)  )_)  )_)                       "
        line_3 = "  _  _  _ ___     )___))___))___)       __ _    ___ _  "
        line_4 = " |_)/ \|_) |     )____)____)_____)     |_ / \|   | / \ "
        line_5 = " |  \_/| \ |  _____|____|____|_______  |  \_/|___|_\_/ "
        line_6 = "               \___________________/                   "

        lines = [line_1, line_2, line_3, line_4, line_5, line_6]

        for line in lines:
            print(line)

    def start(self):
        """Start applications running."""

        while True:

            try:
                self.clear_terminal()

                self.print_banner()
                print("Version 0.4")

                self.print_overview_table()

                print("[a] Add Holding")
                print("[b] Remove Holding")
                print("[c] Update Holding")
                print("[d] Update Price")
                print("[e] Exit")

                print()

                level_1_option = input("Enter an option: ").strip()

                if level_1_option == "e":
                    self.db.close()
                    break
                elif level_1_option == "b":  # Remove holding
                    level_2_option = input("Which holding? ").strip()
                    self.clear_terminal()
                    self.print_single_holding_overview(level_2_option)
                    print()
                    print("[a] Delete all")
                    print("[b] Back")
                    print()
                    level_3_option = input("What would you like to delete? ").strip()
                    if level_3_option == "a":
                        self.remove_all_positions(level_2_option)
                    else:
                        self.remove_position(int(level_2_option), int(level_3_option))

                elif level_1_option == "c":  # Update holding
                    level_2_option = input("Which holding? ").strip()
                    self.clear_terminal()
                    self.print_single_holding_overview(level_2_option)
                    print()
                    level_3_option = input("What would you like to update? ").strip()
                    print("[a] Quantity")
                    print("[b] Buy Price")
                    level_4_option = input("Which would you like to update? ").strip()
                    if level_4_option == "a":
                        quantity = input("Quantity: ").strip()
                        self.update_position_quantity(
                            level_2_option, level_3_option, float(quantity)
                        )
                    elif level_4_option == "b":
                        buy_price = input("Buy Price: ")
                        self.update_position_buy_price(
                            level_2_option, level_3_option, float(buy_price)
                        )

                elif level_1_option == "d":  # Update price
                    level_2_option = input("Which holding? ").strip()
                    current_price = input("Current Price: ").strip()
                    self.update_holding_price(level_2_option, float(current_price))

                elif level_1_option == "a":  # Add holding
                    holding = input("Name: ").strip()
                    quantity = input("Quantity: ").strip()
                    buy_price = input("Buy Price: ").strip()
                    current_price = input("Current Price: ").strip()

                    self.create_position(holding, float(quantity), float(buy_price))
                    # Check that the floats in the line above are necessary

                    self.create_current_price(holding, float(current_price))

                else:

                    while True:
                        self.clear_terminal()
                        print()

                        self.print_single_holding_overview(level_1_option)
                        print()
                        print("[a] Back")
                        print()
                        level_2_option = input("Enter an option: ").strip()
                        if level_2_option == "a":
                            break

            except Exception:
                logging.debug("Exception on main loop", exc_info=True)


Portfolio().start()
