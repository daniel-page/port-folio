"""

Port-Folio

An application for tracking investments.

"""


# TODO:
# Strip whitespace on text entry, if nothing is entered
# Add dates to holdings
# Add cost basis
# List order
# Stocks splits etc
# Add option for deleting an entire holding

import sqlite3 as sqlite
import os
from tabulate import tabulate


class Portfolio:
    """Functions for the Port-Folio application."""

    def __init__(self):
        self.db = sqlite.connect("my-test.db")
        self.create_positions_sql_table()
        self.create_prices_sql_table()

    def create_positions_sql_table(self):
        """Create an SQLite table if it does not already exist."""

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
        """Create an SQLite table if it does not already exist."""

        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS PRICES (
                holding TEXT,
                current_price FLOAT
            );
            """
        )

    def create_position(self, holding, quantity, price):
        """_summary_"""
        self.db.execute(
            f"INSERT INTO POSITIONS (holding, quantity, buy_price) VALUES ('{holding}', {quantity:.2f}, {price:.2f});"
        )
        self.db.commit()

    def remove_position(self, list_number):
        """This is a test."""

        self.db.execute(
            f"DELETE FROM PRICES WHERE holding = (SELECT holding FROM POSITIONS LIMIT 1 OFFSET {list_number-1});"
        )

        self.db.execute(
            f"DELETE FROM POSITIONS WHERE id = (SELECT id FROM POSITIONS LIMIT 1 OFFSET {list_number-1});"
        )

        self.db.commit()

    def create_current_price(self, holding, current_price):
        """_summary_"""

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

    def create_overview_as_table(self, sql_data):
        """_summary_"""
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
        """_summary_"""
        os.system("cls||clear")

    def print_overview_table(self):
        """_summary_"""

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
        """_summary_

        Args:
            holding (_type_): _description_
        """
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
        """Test"""
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

    def start(self):
        """Test"""

        while True:

            self.clear_terminal()

            print(
                """      
                   |    |    |                 
                  )_)  )_)  )_)              
 _  _  _ ___     )___))___))___)       __ _    ___ _ 
|_)/ \|_) |     )____)____)_____)     |_ / \|   | / \\     
|  \_/| \ |  _____|____|____|_______  |  \_/|___|_\_/  
              \___________________/                          
                """
            )
            print("Version 0.2")

            self.print_overview_table()

            print("[a] Add Holding")
            print("[b] Remove Holding")
            print("[c] Update Holding")
            print("[d] Exit")

            print()

            level_1_option = input("Enter an option: ")

            if level_1_option == "d":
                self.db.close()
                break
            elif level_1_option == "b":
                holding = input("Which holding?: ")
                self.clear_terminal()
                self.print_single_holding_overview(holding)
                level_2_option = input("Which would you like to delete? ")
                self.remove_position(int(level_2_option))

            elif level_1_option == "c":
                print("test")
                while True:
                    ...
            elif level_1_option == "a":
                holding = input("Name: ")
                quantity = input("Quantity: ")
                buy_price = input("Buy Price: ")
                current_price = input("Current Price: ")

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
                    level_2_option = input("Enter an option: ")
                    if level_2_option == "a":
                        break


Portfolio().start()
