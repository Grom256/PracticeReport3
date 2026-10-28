from selenium import webdriver
from selenium.webdriver.common.by import By
import pytest_check as check

driver = webdriver.Firefox()
driver.get("http://127.0.0.1:8000/catalog/")
print(driver.title)
print(driver.current_url)

assert "Каталог" in driver.title
product_link = driver.find_element(By.XPATH, "//a[contains(@class,'card-link-overlay')]")
product_name = product_link.text
print(product_name)
href = product_link.get_attribute("href")
print(href)

assert "products" in href
product_link.click()
heading = driver.find_element(By.XPATH, "//h1")
print(heading.text)
print(driver.title)

check.is_true(heading.is_displayed())
check.equal(heading.text, product_name)
check.is_in(product_name, driver.title)
check.is_in("products", driver.current_url)
input()
driver.quit()