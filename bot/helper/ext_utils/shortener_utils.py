from base64 import b64encode
from random import choice, random
from asyncio import sleep as asleep
from urllib.parse import quote

from cloudscraper import create_scraper
from urllib3 import disable_warnings

from ... import LOGGER, shortener_dict


async def short_url(longurl, attempt=0):
    if not shortener_dict:
        LOGGER.warning("shortener_dict is empty. Returning original URL.")
        return longurl
    if attempt >= 4:
        LOGGER.error(f"Max attempts reached while shortening URL: {longurl}")
        return longurl

    _shortener, _shortener_api = choice(list(shortener_dict.items()))
    LOGGER.debug(f"Using shortener: {_shortener} | Attempt: {attempt}")
    cget = create_scraper().request
    disable_warnings()

    try:
        if "shorte.st" in _shortener:
            headers = {"public-api-token": _shortener_api}
            data = {"urlToShorten": quote(longurl)}
            LOGGER.debug(f"Trying shorte.st with data: {data}")
            response = cget(
                "PUT", "https://api.shorte.st/v1/data/url", headers=headers, data=data
            ).json()
            LOGGER.debug(f"shorte.st response: {response}")
            return response.get("shortenedUrl", longurl)

        elif "linkvertise" in _shortener:
            url = quote(b64encode(longurl.encode("utf-8")))
            linkvertise = [
                f"https://link-to.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
                f"https://up-to-down.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
                f"https://direct-link.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
                f"https://file-link.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
            ]
            shorted = choice(linkvertise)
            LOGGER.debug(f"Generated linkvertise URL: {shorted}")
            return shorted

        elif "bitly.com" in _shortener:
            headers = {"Authorization": f"Bearer {_shortener_api}"}
            LOGGER.debug("Sending to Bitly")
            response = cget(
                "POST",
                "https://api-ssl.bit.ly/v4/shorten",
                json={"long_url": longurl},
                headers=headers,
            ).json()
            LOGGER.debug(f"Bitly response: {response}")
            return response.get("link", longurl)

        elif "ouo.io" in _shortener:
            LOGGER.debug("Using ouo.io shortener")
            response = cget(
                "GET", f"http://ouo.io/api/{_shortener_api}?s={longurl}", verify=False
            ).text
            LOGGER.debug(f"ouo.io response: {response}")
            return response

        elif "cutt.ly" in _shortener:
            LOGGER.debug("Using cutt.ly shortener")
            response = cget(
                "GET",
                f"http://cutt.ly/api/api.php?key={_shortener_api}&short={longurl}",
            ).json()
            LOGGER.debug(f"cutt.ly response: {response}")
            return response.get("url", {}).get("shortLink", longurl)

        elif "earn4link.in" in _shortener:
            LOGGER.debug("Using earn4link.in shortener")
            response = cget(
                "GET",
                f"https://earn4link.in/api?api={_shortener_api}&url={quote(longurl)}",
                verify=False
            ).json()
            LOGGER.debug(f"earn4link.in response: {response}")
            return response.get("shortenedUrl", longurl)

        else:
            LOGGER.debug(f"Trying generic shortener: {_shortener}")
            response = cget(
                "GET",
                f"https://{_shortener}/api?api={_shortener_api}&url={quote(longurl)}",
            ).json()
            LOGGER.debug(f"Primary response: {response}")
            shorted = response.get("shortenedUrl")

            if not shorted:
                LOGGER.warning("Primary shortener failed, trying shrtco.de fallback")
                shrtco_res = cget(
                    "GET", f"https://api.shrtco.de/v2/shorten?url={quote(longurl)}"
                ).json()
                LOGGER.debug(f"shrtco.de response: {shrtco_res}")
                shrtco_link = shrtco_res.get("result", {}).get("full_short_link")
                if shrtco_link:
                    response = cget(
                        "GET",
                        f"https://{_shortener}/api?api={_shortener_api}&url={shrtco_link}",
                    ).json()
                    LOGGER.debug(f"Fallback response: {response}")
                    shorted = response.get("shortenedUrl")

            return shorted if shorted else longurl

    except Exception as e:
        LOGGER.error(f"Error in short_url: {e}", exc_info=True)
        await asleep(0.8)
        return await short_url(longurl, attempt + 1)
