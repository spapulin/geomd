import pytest
import textwrap


@pytest.fixture
def geojson_feature_collection() -> str:
    return """\
        {
            "type": "FeatureCollection",
            "title": "Barcelona Tour",
            "features": [
                {
                    "type": "Feature",
                    "title": "Park Güell",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [2.1527, 41.4145]
                    },
                    "properties": {
                        "id": "1",
                        "author": "Adam Smith",
                        "overview": "A colorful park designed by Antoni Gaudí",
                        "address": "Carrer d'Olot, Barcelona, Spain",
                        "title": "Park Güell"
                    }
                },
                {
                    "type": "Feature",
                    "title": "Casa Batlló",
                    "geometry": {"type": "Point", "coordinates": [2.16487, 41.391642]},
                    "properties": {
                        "id": "2",
                        "author": "Adam Smith",
                        "overview": "Casa Batlló is a renowned building on Passeig de Gràcia, remodeled by Antoni Gaudí between 1904 and 1906",
                        "address": "Passeig de Gràcia, 43, Barcelona, Spain",
                        "title": "Casa Batlló"
                    }
                }
            ]
        }"""


@pytest.fixture
def geomd_feature_collection() -> str:
    return textwrap.dedent("""\
        # Barcelona Tour
    
        ## Park Güell
        
        <!--
        field_mapping:
            - On map: geometry
        -->
        
        ### Overview
        
        Park Güell is a public park system composed of gardens and architectural elements located on Carmel Hill
        
        ### Address
        
        Carrer d'Olot, Barcelona, Spain
        
        ### On map
        
        ```geometry
        {
            "type": "Point",
            "coordinates": [2.152777, 41.414444]
        }
        ```
        
        ## Casa Batlló
        
        <!--
        field_mapping:
            - On map: geometry
        -->

        ### Overview
        
        Casa Batlló is a renowned building on Passeig de Gràcia, remodeled by Antoni Gaudí between 1904 and 1906
        
        ### Address
        
        Passeig de Gràcia, 43, Barcelona, Spain
        
        ### On map
        
        ```geometry
        {
            "type": "Point",
            "coordinates": [2.16487, 41.391642]
        }
        ```
    """)