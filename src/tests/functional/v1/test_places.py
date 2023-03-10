import pytest
from starlette import status

from models import Place
from repositories.places_repository import PlacesRepository


@pytest.mark.usefixtures("session")
class TestPlacesCreateMethod:
    """
    Тестирование метода создания любимого места.
    """

    @staticmethod
    async def get_endpoint() -> str:
        """
        Получение адреса метода API.

        :return:
        """

        return "/api/v1/places"

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("event_producer_publish")
    async def test_method_success(self, client, session, httpx_mock):
        """
        Тестирование успешного сценария.

        :param client: Фикстура клиента для запросов.
        :param session: Фикстура сессии для работы с БД.
        :param httpx_mock: Фикстура запроса на внешние API.
        :return:
        """

        mock_response = {
            "city": "City",
            "countryCode": "AA",
            "locality": "Location",
        }
        # замена настоящего ответа от API на "заглушку" для тестирования
        # настоящий запрос на API не производится
        httpx_mock.add_response(json=mock_response)

        # передаваемые данные
        request_body = {
            "latitude": 12.3456,
            "longitude": 23.4567,
            "description": "Описание тестового места",
        }
        # осуществление запроса
        response = await client.post(
            await self.get_endpoint(),
            json=request_body,
        )

        # проверка корректности ответа от сервера
        assert response.status_code == status.HTTP_201_CREATED

        response_json = response.json()
        assert "data" in response_json
        assert isinstance(response_json["data"]["id"], int)
        assert isinstance(response_json["data"]["created_at"], str)
        assert isinstance(response_json["data"]["updated_at"], str)
        assert response_json["data"]["latitude"] == request_body["latitude"]
        assert response_json["data"]["longitude"] == request_body["longitude"]
        assert response_json["data"]["description"] == request_body["description"]
        assert response_json["data"]["country"] == mock_response["countryCode"]
        assert response_json["data"]["city"] == mock_response["city"]
        assert response_json["data"]["locality"] == mock_response["locality"]

        # проверка существования записи в базе данных
        created_data = await PlacesRepository(session).find_all_by(
            latitude=request_body["latitude"],
            longitude=request_body["longitude"],
            description=request_body["description"],
            limit=100,
        )
        assert len(created_data) == 1
        assert isinstance(created_data[0], Place)
        assert created_data[0].latitude == request_body["latitude"]
        assert created_data[0].longitude == request_body["longitude"]
        assert created_data[0].description == request_body["description"]
        assert created_data[0].country == mock_response["countryCode"]
        assert created_data[0].city == mock_response["city"]
        assert created_data[0].locality == mock_response["locality"]

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("event_producer_publish")
    async def test_auto(self, client, session, httpx_mock):
        """
        Тестирование автоматического определения локации.

        :param client: Фикстура клиента для запросов.
        :param session: Фикстура сессии для работы с БД.
        :param httpx_mock: Фикстура запроса на внешние API.
        :return:
        """

        mock_response = {
            "city": "Perm",
            "countryCode": "Ru",
            "locality": "Location",
        }
        # замена настоящего ответа от API на "заглушку" для тестирования
        # настоящий запрос на API не производится
        httpx_mock.add_response(json=mock_response)

        # передаваемые данные
        request_body = {
            "description": "Описание тестового места",
        }

        latlng = [58.0105, 56.2502]

        # осуществление запроса
        response = await client.post(
            await self.get_endpoint() + "/auto",
            json=request_body,
        )

        # проверка корректности ответа от сервера
        assert response.status_code == status.HTTP_201_CREATED

        response_json = response.json()
        assert "data" in response_json
        assert isinstance(response_json["data"]["id"], int)
        assert isinstance(response_json["data"]["created_at"], str)
        assert isinstance(response_json["data"]["updated_at"], str)
        assert response_json["data"]["latitude"] == latlng[0]
        assert response_json["data"]["longitude"] == latlng[1]
        assert response_json["data"]["description"] == request_body["description"]
        assert response_json["data"]["country"] == mock_response["countryCode"]
        assert response_json["data"]["city"] == mock_response["city"]
        assert response_json["data"]["locality"] == mock_response["locality"]

        # проверка существования записи в базе данных
        created_data = await PlacesRepository(session).find_all_by(
            latitude=latlng[0],
            longitude=latlng[1],
            description=request_body["description"],
            limit=100,
        )
        assert len(created_data) == 1
        assert isinstance(created_data[0], Place)
        assert created_data[0].latitude == latlng[0]
        assert created_data[0].longitude == latlng[1]
        assert created_data[0].description == request_body["description"]
        assert created_data[0].country == mock_response["countryCode"]
        assert created_data[0].city == mock_response["city"]
        assert created_data[0].locality == mock_response["locality"]

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("event_producer_publish")
    async def test_delete(self, client, session, httpx_mock):
        """
        Тестирование удаления локации.

        :param client: Фикстура клиента для запросов.
        :param session: Фикстура сессии для работы с БД.
        :param httpx_mock: Фикстура запроса на внешние API.
        :return:
        """
        request_body = {
            "latitude": 12.3456,
            "longitude": 23.4567,
            "description": "Описание тестового места",
            "city": "City",
            "country": "AA",
            "locality": "Location",
        }
        created_data = await PlacesRepository(session).create_model(request_body)

        response = await client.delete((await self.get_endpoint()) + f"/{created_data}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = await client.get((await self.get_endpoint()) + f"/{created_data}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
