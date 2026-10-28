from selenium import webdriver
from selenium.webdriver.common.by import By
import pytest_check as check

driver = webdriver.Firefox()
driver.get("http://127.0.0.1:8000/accounts/login/")
print(driver.title)
print(driver.current_url)

assert "Вхід" in driver.title
heading = driver.find_element(By.XPATH, "//h1")
print(heading.text)

check.is_true(heading.is_displayed())
driver.find_element(By.ID, "id_username").send_keys("GromAdmin")
driver.find_element(By.ID, "id_password").send_keys("Victory164!")
driver.find_element(By.XPATH, "//button[contains(normalize-space(.),'Увійти')]").click()
profile_heading = driver.find_element(By.XPATH, "//h1")

print(profile_heading.text)
print(driver.current_url)

check.is_true(profile_heading.is_displayed())
check.is_in("profile", driver.current_url)
input()
driver.quit()