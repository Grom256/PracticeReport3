# GromBricks

Навчальний інтернет-магазин LEGO-мініфігурок і окремих деталей на Django та MySQL.

## Локальний запуск

Потрібні Python, MySQL Server 8.4 або новіший і база даних `grombrick` з кодуванням `utf8mb4`. Django 6.1 підтримує MySQL від 8.4. Структуру таблиць створюють Django migrations; вручну створювати таблиці в MySQL Workbench не потрібно.

У MySQL Workbench створіть базу даних:

```sql
CREATE DATABASE grombrick CHARACTER SET utf8mb4;
```

Для застосунку рекомендовано створити окремого користувача MySQL з правами лише на цю базу.

У PowerShell з кореня репозиторію задайте параметри підключення. Пароль не додавайте до Git:

```powershell
$env:MYSQL_DATABASE = 'grombrick'
$env:MYSQL_USER = 'grombricks_app'
$env:MYSQL_PASSWORD = 'ваш_локальний_пароль'
$env:MYSQL_HOST = '127.0.0.1'
$env:MYSQL_PORT = '3306'
```

Потім перейдіть до папки проєкту й виконайте:

```powershell
cd GromBricks
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py createsuperuser
..\.venv\Scripts\python.exe manage.py runserver
```

Для наступних сеансів PowerShell змінні середовища потрібно задати знову або налаштувати постійно у Windows. Django Admin відкривається за адресою `/admin/`.

## Структура даних

- `Category` — тематичні категорії товарів, наприклад серії LEGO.
- `Product` — мініфігурки й деталі з ціною, станом, залишком та ознакою рідкісного товару.
- `Order` — покупець, адреса, служба доставки, спосіб оплати та статус.
- `OrderItem` — склад замовлення з ціною товару на момент покупки.
- Облікові записи використовують стандартну систему автентифікації Django; кошик планується зберігати в сесії.

Оплата в навчальній версії фіксується як переказ на картку або рахунок. Банківські реквізити картки покупця не збираються, а реальний платіжний сервіс не підключений.
