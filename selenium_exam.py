# Version One. Without database Querys working with pandas for sql insertions

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.keys import Keys
# import time
# import pandas as pd
# from sqlalchemy import create_engine

# # Configurar el servicio de ChromeDriver
# service = Service(executable_path="chromedriver.exe")
# driver = webdriver.Chrome(service=service)

# driver.get("https://www.airbnb.com")

# # Extraer los datos de la página
# titulos = driver.find_elements(By.XPATH, '//div[@data-testid="listing-card-title"]')
# precios = driver.find_elements(By.XPATH, '//div[@class="_i5duul"]')
# valoraciones = driver.find_elements(By.XPATH, '//div[@class="t1a9j9y7 atm_da_1ko3t4y atm_dm_kb7nvz atm_fg_h9n0ih dir dir-ltr"]')

# print(f"Tamaño de titulos: {len(titulos)}")
# print(f"Tamaño de precios: {len(precios)}")
# print(f"Tamaño de valoraciones: {len(valoraciones)}")
# # Crear un DataFrame de pandas para organizar los datos
# data = {'Titulo': [titulo.text for titulo in titulos],
#         'Precio': [precio.text for precio in precios],
#         'Valoracion': [valoracion.text for valoracion in valoraciones]}
# df = pd.DataFrame(data)

# # Imprimir el DataFrame para verificar los datos
# print(df)

# # Conectar a la base de datos MySQL con SQLAlchemy
# engine = create_engine('mysql+mysqlconnector://root:@localhost/selenium')

# # Crear la tabla en la base de datos
# df.to_sql(name='airbnb_titles', con=engine, if_exists='replace', index=False)

# # Cerrar el navegador
# driver.quit()

import mysql.connector
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from time import sleep

class AirbnbDataExtractor:
    def __init__(self, url, retries=5):
        self.url = url
        self.retries = retries

    def extract_data(self):
        """
        Extracts title, price, and rating data from an Airbnb page.

        Returns:
        - DataFrame: A pandas DataFrame with the extracted data.
        """
        for _ in range(self.retries):
            service = Service(executable_path="chromedriver.exe")
            driver = webdriver.Chrome(service=service)

            driver.get(self.url)

            try:
                titles = driver.find_elements(By.XPATH, '//div[@data-testid="listing-card-title"]')
                prices = driver.find_elements(By.XPATH, '//div[@class="_i5duul"]')
                ratings = driver.find_elements(By.XPATH, '//div[@class="t1a9j9y7 atm_da_1ko3t4y atm_dm_kb7nvz atm_fg_h9n0ih dir dir-ltr"]')

                if len(titles) != len(prices) or len(titles) != len(ratings):
                    raise ValueError("All arrays must be of the same length")

                data = {'Title': [title.text for title in titles],
                        'Price': [price.text for price in prices],
                        'Rating': [rating.text for rating in ratings]}
                df = pd.DataFrame(data)

                # Extract average rating
                df['AverageRating'] = df['Rating'].apply(lambda x: float(x.split(':')[1].split(' ')[1]) if ':' in x and len(x.split(':')) >= 2 else 0)


                driver.quit()
                return df

            except ValueError as e:
                print(f"Error: {e}")
                driver.quit()
                print(f"Retrying ({_ + 1}/{self.retries})...")
                sleep(1)

        print("Maximum number of retries reached. Failed to extract data.")
        return None

    def insert_data_to_db(self, df, table_name):
        """
        Inserts the extracted data from a DataFrame into a database table.

        Args:
        - df (DataFrame): A pandas DataFrame with the extracted data.
        - table_name (str): The name of the table in the database.

        Returns:
        - bool: True if insertion was successful, False otherwise.
        """
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="selenium"
        )
        cursor = connection.cursor()

        try:
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                Title VARCHAR(255),
                Price VARCHAR(50),
                Rating VARCHAR(50),
                AverageRating FLOAT
            );
            """
            cursor.execute(create_table_query)
            connection.commit()

            data_tuples = [tuple(row) for row in df.itertuples(index=False)]

            insert_query = f"""
            INSERT INTO {table_name} (Title, Price, Rating, AverageRating)
            VALUES (%s, %s, %s, %s)
            """
            cursor.executemany(insert_query, data_tuples)
            connection.commit()

            return True

        except mysql.connector.Error as error:
            print(f"Error inserting data into table: {error}")
            return False

        finally:
            cursor.close()
            connection.close()

# Usage
extractor = AirbnbDataExtractor(url="https://www.airbnb.com", retries=5)

# Extract data
data_df = extractor.extract_data()

if data_df is not None:
    # Insert data into database
    success = extractor.insert_data_to_db(data_df, "airbnb_examples")
    if success:
        print("Data inserted successfully into the database.")
    else:
        print("Error inserting data into the database.")
else:
    print("Failed to extract data.")
