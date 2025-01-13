from urllib.request import urlopen, Request
import pendulum
import ssl


def test_url():
    # Configuration de l'URL
    base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/"
    filename = "yellow_tripdata"
    extension = ".parquet"

    # Tester les mois depuis août
    for offset in range(5):  # Tester les 5 derniers mois (ajustez selon vos besoins)
        month = pendulum.now().subtract(months=offset).format('YYYY-MM')
        full_url = f"{base_url}{filename}_{month}{extension}"

        print(f"Testing URL: {full_url}")

        # Désactiver la vérification SSL (à ne pas utiliser en production)
        ssl_context = ssl._create_unverified_context()

        try:
            # Ajouter un User-Agent
            req = Request(
                full_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
                }
            )

            # Tester l'accès à l'URL
            with urlopen(req, context=ssl_context) as response:
                print(f"Success! File is accessible for {month}. HTTP Status Code: {response.status}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
        except Exception as e:
            print(f"Failed to access the URL for {month}: {str(e)}")


# Exécuter la fonction de test
test_url()
