from .base import BaseProvider
from backend.models import WordClue

MOCK_TOPICS: dict[str, list[dict[str, str]]] = {
    "default": [
        {"word": "PYTHON", "clue": "Popular programming language named after a snake"},
        {"word": "ALGORITHM", "clue": "Step-by-step procedure for solving a problem"},
        {"word": "VARIABLE", "clue": "Named storage location in code"},
        {"word": "FUNCTION", "clue": "Reusable block of code"},
        {"word": "LOOP", "clue": "Repeated execution of a block"},
        {"word": "ARRAY", "clue": "Ordered collection of elements"},
        {"word": "STRING", "clue": "Sequence of characters"},
        {"word": "CLASS", "clue": "Blueprint for creating objects"},
        {"word": "DEBUG", "clue": "Finding and fixing errors in code"},
        {"word": "STACK", "clue": "Last-in-first-out data structure"},
        {"word": "QUEUE", "clue": "First-in-first-out data structure"},
        {"word": "BINARY", "clue": "Base-two number system"},
        {"word": "SYNTAX", "clue": "Rules governing code structure"},
        {"word": "COMPILE", "clue": "Translate source code to machine code"},
        {"word": "PARSE", "clue": "Analyze a string according to grammar rules"},
        {"word": "OBJECT", "clue": "Instance of a class"},
        {"word": "METHOD", "clue": "Function belonging to a class"},
        {"word": "IMPORT", "clue": "Bring in code from another module"},
        {"word": "RETURN", "clue": "Send a value back from a function"},
        {"word": "INDEX", "clue": "Position of an element in a sequence"},
        {"word": "CACHE", "clue": "Temporary storage for fast access"},
        {"word": "HASH", "clue": "Fixed-size output from a mapping function"},
        {"word": "TOKEN", "clue": "Smallest meaningful unit in parsing"},
        {"word": "NODE", "clue": "Element in a tree or linked list"},
        {"word": "GRAPH", "clue": "Network of vertices and edges"},
        {"word": "PIXEL", "clue": "Smallest unit of a digital image"},
        {"word": "QUERY", "clue": "Request for data from a database"},
        {"word": "ROUTE", "clue": "URL path mapped to a handler"},
        {"word": "SCOPE", "clue": "Region where a variable is accessible"},
        {"word": "TRAIT", "clue": "Shared behavior definition in Rust"},
    ],
    "animals": [
        {"word": "ELEPHANT", "clue": "Largest living land animal"},
        {"word": "DOLPHIN", "clue": "Intelligent marine mammal"},
        {"word": "PENGUIN", "clue": "Flightless bird of the southern hemisphere"},
        {"word": "GIRAFFE", "clue": "Tallest living terrestrial animal"},
        {"word": "TIGER", "clue": "Largest species of the cat family"},
        {"word": "EAGLE", "clue": "Large bird of prey with keen eyesight"},
        {"word": "WHALE", "clue": "Largest animal ever to have lived"},
        {"word": "COBRA", "clue": "Venomous snake that spreads a hood"},
        {"word": "KOALA", "clue": "Australian marsupial that eats eucalyptus"},
        {"word": "OTTER", "clue": "Playful aquatic mammal"},
        {"word": "FALCON", "clue": "Fastest animal in the world"},
        {"word": "PANDA", "clue": "Black and white bear from China"},
        {"word": "GECKO", "clue": "Small lizard that can walk on walls"},
        {"word": "HERON", "clue": "Long-legged wading bird"},
        {"word": "BISON", "clue": "Large grazing mammal of North America"},
        {"word": "LEMUR", "clue": "Primate found only in Madagascar"},
        {"word": "CRANE", "clue": "Tall bird known for elaborate dances"},
        {"word": "MOOSE", "clue": "Largest member of the deer family"},
        {"word": "SQUID", "clue": "Ten-armed marine cephalopod"},
        {"word": "RAVEN", "clue": "Large, intelligent black bird"},
    ],
    "space": [
        {"word": "GALAXY", "clue": "Massive system of stars and planets"},
        {"word": "NEBULA", "clue": "Cloud of gas and dust in space"},
        {"word": "QUASAR", "clue": "Extremely luminous active galactic nucleus"},
        {"word": "COMET", "clue": "Icy body that develops a tail near the sun"},
        {"word": "ORBIT", "clue": "Curved path around a celestial body"},
        {"word": "METEOR", "clue": "Streak of light from space debris"},
        {"word": "PULSAR", "clue": "Rapidly rotating neutron star"},
        {"word": "PLANET", "clue": "Celestial body orbiting a star"},
        {"word": "LUNAR", "clue": "Relating to the moon"},
        {"word": "SOLAR", "clue": "Relating to the sun"},
        {"word": "ROCKET", "clue": "Vehicle propelled by expelled gases"},
        {"word": "GRAVITY", "clue": "Force attracting bodies with mass"},
        {"word": "ECLIPSE", "clue": "One body passing into another's shadow"},
        {"word": "SATURN", "clue": "Ringed gas giant planet"},
        {"word": "VENUS", "clue": "Hottest planet in our solar system"},
        {"word": "COSMOS", "clue": "The universe regarded as an ordered system"},
        {"word": "ASTEROID", "clue": "Rocky body orbiting between Mars and Jupiter"},
        {"word": "ZENITH", "clue": "Point directly overhead in the sky"},
        {"word": "NOVA", "clue": "Star showing a sudden increase in brightness"},
        {"word": "DWARF", "clue": "Type of small, dense star"},
    ],
}


class MockProvider(BaseProvider):
    async def generate_words(self, topic: str, count: int, max_length: int) -> list[WordClue]:
        topic_lower = topic.lower()
        pairs = None
        for key in MOCK_TOPICS:
            if key in topic_lower or topic_lower in key:
                pairs = MOCK_TOPICS[key]
                break
        if pairs is None:
            pairs = MOCK_TOPICS["default"]

        filtered = [p for p in pairs if len(p["word"]) <= max_length]
        selected = filtered[:count]
        return [WordClue(word=p["word"].upper(), clue=p["clue"]) for p in selected]
