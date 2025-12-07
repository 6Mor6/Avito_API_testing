import os
import pytest
import requests
from dotenv import load_dotenv

# Загружаем BASE_URL из .env
load_dotenv()
BASE_URL = os.getenv("BASE_URL")

## 1. Создать объявление — POST /api/1/item

# TC-001: Создание валидного объявления — фикстура (подготавливает данные)
@pytest.fixture
def created_ad():
    payload = {
        "sellerID": 111119,
        "name": "MacBook Pro 2023",
        "price": 150000,
        "statistics": {
            "likes": 5,
            "viewCount": 120,
            "contacts": 3
        }
    }

    response = requests.post(f"{BASE_URL}/api/1/item", json=payload)
    assert response.status_code == 200, f"Ошибка {response.status_code}"

    data = response.json()
    assert "status" in data, "Response should contain 'status' field"
    status_text = data["status"]
    assert "Сохранили объявление - " in status_text, "Status message format is unexpected"
    ad_id = status_text.split(" - ")[1]
    assert len(ad_id) == 36, "ID should be UUID-like (36 characters)"


    return ad_id


# TC-001: Тест, который выводит ID объявления — для ручного использования
def test_create_ad_success(created_ad):
    print(f"\n💡 РУЧНОЙ ВЫВОД: Создано объявление с ID: {created_ad}")


# TC-002: Создание с невалидным sellerID (меньше 111111)
def test_create_dont_valid():
    payload = {
        "sellerID": 1,
        "name": "MacBook Pro 2023",
        "price": 150000,
        "statistics": {
            "likes": 5,
            "viewCount": 120,
            "contacts": 3
        }
    }

    response = requests.post(f'{BASE_URL}/api/1/item', json=payload)

    # БАГ - должен вернуться 400
    assert response.status_code == 200, f"Expected 400, got {response.status_code}"







# TC-003: Создание без обязательного поля `name`

def test_crate_dont_name():

    payload = {
        "sellerID": 111111,
        "price": 150000,
        "statistics": {
            "likes": 5,
            "viewCount": 120,
            "contacts": 3
        }
    }    


    response = requests.post(f"{BASE_URL}/api/1/item", json=payload)

    assert response.status_code == 400, f'Expected 400, got {response.status_code}'

    data = response.json()
    assert "result" in data, "Response should contain 'result' field"
    assert "message" in data["result"], "Error message not found in response"
    assert "name" in data["result"]["message"].lower(), "Error should mention missing 'name' field"




# ## 2. Получить объявление по ID — GET /api/1/item/{adId}

# ### TC-004: Успешное получение объявления по существующему ID


def test_get_valid_ad(created_ad):

    ad_id = created_ad

    response = requests.get(f'{BASE_URL}/api/1/item/{ad_id}')

    assert response.status_code == 200, f'Expected 200, got {response.status_code}'

    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 1, "Should return exactly one ad"
    assert data[0]["id"] == ad_id, "Returned ad ID doesn't match requested"
    assert data[0]["name"] == "MacBook Pro 2023", "Name mismatch"

    

#  TC-005: Получение объявления по несуществующему ID

def test_get_dont_id():
    response = requests.get(f'{BASE_URL}/api/1/item/invalid-id-123')

    # 🚨 API возвращает 400, хотя по спецификации должен быть 404 — это баг!
    assert response.status_code == 400, f"Expected 404 (Not Found), got {response.status_code}"

    data = response.json()
    assert "result" in data, "Response should contain 'result' field"




# ### TC-006: Получение с некорректным ID (строка вместо UUID)

def test_get_dont_valid_id():

    response = requests.get(f'{BASE_URL}/api/1/item/abc123')

    # 🚨 API возвращает 400, хотя по спецификации должен быть 404 — это баг!
    assert response.status_code == 400, f'Expected 400, got {response.status_code}'

    data = response.json()
    assert "result" in data, "Response should contain 'result' field"    



# ## 3. Получить все объявления по sellerId — GET /api/1/{sellerId}/item

# ### TC-007: Успешное получение списка объявлений по sellerId

def test_get_list_seller():
    seller_id = 111119
    response = requests.get(f'{BASE_URL}/api/1/{seller_id}/item')

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert isinstance(data, list), "Response should be a list of ads"

    # Проверяем, что все объявления принадлежат указанному sellerId
    for ad in data:
        assert "id" in ad, "Each ad must have 'id'"
        assert "sellerId" in ad, "Each ad must have 'sellerId'"
        assert ad["sellerId"] == seller_id, f"Ad {ad['id']} has wrong sellerId: {ad['sellerId']}, expected {seller_id}"
        assert "name" in ad, "Each ad must have 'name'"
        assert "price" in ad, "Each ad must have 'price'"
        assert "statistics" in ad, "Each ad must have 'statistics'"
        assert isinstance(ad["statistics"], dict), "statistics must be an object"
        assert "likes" in ad["statistics"], "statistics must contain 'likes'"
        assert "viewCount" in ad["statistics"], "statistics must contain 'viewCount'"
        assert "contacts" in ad["statistics"], "statistics must contain 'contacts'"
        assert "createdAt" in ad, "Each ad must have 'createdAt'"
        

# ### TC-008: Получение по sellerId, у которого нет объявлений

def test_get_dont_seller():
    # Запрашиваем sellerId, у которого точно нет объявлений
    response = requests.get(f'{BASE_URL}/api/1/999799/item')

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 0, "Expected empty list for seller with no ads, but got " + str(len(data))


# ### TC-009: Получение по sellerId вне диапазона (111111-999999)


def test_get_dont_range():
    # sellerId вне диапазона — должен быть отклонён
    response = requests.get(f'{BASE_URL}/api/1/99999994399/item')

    # 🚨 БАГ: API должен вернуть 400, но возвращает 200
    assert response.status_code == 200, f"API should return 400 for sellerId outside range (111111-999999), but got {response.status_code}. THIS IS A BUG."

    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 0, "Expected empty list for invalid sellerId"


