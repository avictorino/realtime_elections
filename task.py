import json
import os
from dateutil.parser import parse as date_parse
from slugify import slugify
from app_config import celery_app, redis_mayors, logger, redis_cities


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10, slice_mayors_by_city.s())
    sender.add_periodic_task(60, attach_zones_to_mayors.s())


@celery_app.task
def slice_mayors_by_city():
    """
    Essa função deverá fatiar um arquivo de 2mb que contém todas as cidade do país e salvar no REDIS utilizando
    uma parte da URL que o client side irá acessar como chave do cache.
    Os arquivos são enviados pelo governo para uma central que faz o upload no S3 em tempo real
    High frequency offen 10 seconds during the votes counting
    """
    logger.info("STARTING slice_mayors_by_city")

    try:

        released_votes = read_from_mock_s3('/mock_s3/mayors.json')
        cities = get_cities()
        last_update = date_parse(f"{released_votes['last_updated']['date']} {released_votes['last_updated']['time']}")

        if redis_mayors.get("last_mayors_update"):
            last_update_redis = date_parse(redis_mayors.get("last_mayors_update").decode("utf-8"))
            """
            For the testing purpose the mayors.json never will be updated by the government, so will be needed to bypass
            """
            if last_update_redis <= last_update and False:
                logger.info("UPDATE NOT REQUIRED")
                return

        mayors = {}
        for id_city, city in released_votes["municipios"].items():
            state, city_name = cities[id_city]["e"].lower(), slugify(city["nm"])
            mayors[f"/cities/mayors-{state}-{city_name}.json"] = json.dumps(city)

        redis_mayors.set("last_mayors_update", last_update.isoformat())
        redis_mayors.mset(mayors)

    except Exception as ex:
        logger.exception(ex)


@celery_app.task
def attach_zones_to_mayors():

    logger.info("STARTING attach_zones_to_mayors")
    """
        A razão dessa função ser executada em outro momento é por causa da frequencia que o governo libera os dados.
        Como a informação de zonas eleitorias é liberada a cada 1 minuto e os prefeitos a cada 10 segundos não achei prudente
        executar essa funcionalidade a cada 10 segundos.
    """

    try:

        cities = get_cities()

        for city in cities.values():
            city_name, state = slugify(city['n']), city['e'].lower()
            zone = read_from_mock_s3(f"/mock_s3/zone-{state}-{city_name}.json")
            """
            Not will keep >5000 files in the github repo, just keep the major one zone-sp-sao-paulo.json
            """
            if zone:
                mayor_key = f"/cities/mayors-{state}-{city_name}.json"
                mayors_per_city = json.loads(redis_mayors.get(mayor_key))
                mayors_per_city["zone"] = zone
                redis_mayors.set(mayor_key, json.dumps(mayors_per_city))

    except Exception as ex:
        logger.exception(ex)


def read_from_mock_s3(fname: str) -> dict:
    try:
        return json.load(open(os.path.dirname(os.path.abspath(__file__)) + fname))
    except IOError:
        pass


def get_cities():

    cities = redis_cities.get("cities")
    if not cities:
        """
        The content not will change during the vote counts, will be saved in REDIS on the first run
        """
        cities = read_from_mock_s3('/mock_s3/cities.json')
        redis_cities.set("cities", json.dumps(cities))
    else:
        cities = json.loads(cities.decode("utf-8"))

    return cities

if __name__ == '__main__':
    slice_mayors_by_city()
    attach_zones_to_mayors()
