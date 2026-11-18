from datetime import datetime
from app.schemas.coworking import Coworking, Workspace, Location, ZoneType

MOCK_COWORKINGS = [
    Coworking(
        id=1,
        name="CoSpace Podil",
        location=Location(
            latitude=50.4642,
            longitude=30.5187,
            address="вул. Сагайдачного, 25, Київ"
        ),
        total_floors=3,
        rating=4.8,
        workspaces=[
            Workspace(
                id=101, coworking_id=1, floor=1, zone_type=ZoneType.OPEN_SPACE,
                name="Open Space 1-й поверх — Місце #7",
                description="Світла зона з кавовою станцією, розетками та швидким Wi-Fi",
                price_per_hour=50.0, price_per_day=300.0
            ),
            Workspace(
                id=201, coworking_id=1, floor=2, zone_type=ZoneType.SILENT_ZONE,
                name="Silent Zone 2-й поверх — Стіл #12",
                description="Тиха зона для глибокої роботи, ергономічні крісла та лампи",
                price_per_hour=65.0, price_per_day=380.0
            ),
            Workspace(
                id=301, coworking_id=1, floor=3, zone_type=ZoneType.MEETING_ROOM,
                name="Переговорна «Дніпро»",
                description="Кімната на 8 осіб із екраном, маркерною дошкою та відеозв'язком",
                price_per_hour=220.0, price_per_day=1400.0
            ),
        ]
    ),
    Coworking(
        id=2,
        name="CoSpace Pechersk",
        location=Location(
            latitude=50.4271,
            longitude=30.5389,
            address="вул. Басейна, 9, Київ"
        ),
        total_floors=4,
        rating=4.9,
        workspaces=[
            Workspace(
                id=401, coworking_id=2, floor=1, zone_type=ZoneType.OPEN_SPACE,
                name="Lounge 1-й поверх — Диван #3",
                description="Неформальна зона з диванами, кавою та тихою музикою",
                price_per_hour=55.0, price_per_day=320.0
            ),
            Workspace(
                id=501, coworking_id=2, floor=2, zone_type=ZoneType.OPEN_SPACE,
                name="Open Space 2-й поверх — Місце #21",
                description="Великий зал із панорамними вікнами та моніторами на вибір",
                price_per_hour=60.0, price_per_day=340.0
            ),
            Workspace(
                id=601, coworking_id=2, floor=3, zone_type=ZoneType.MEETING_ROOM,
                name="Фон-бокс 3.B",
                description="Звукоізольована капсула для дзвінків і онлайн-мітингів",
                price_per_hour=90.0, price_per_day=550.0
            ),
            Workspace(
                id=701, coworking_id=2, floor=4, zone_type=ZoneType.LECTURE_HALL,
                name="Івент-зал 4-й поверх",
                description="Зал на 40 місць із проєктором, сценою та звуком для презентацій",
                price_per_hour=450.0, price_per_day=2800.0
            ),
        ]
    ),
    Coworking(
        id=3,
        name="CoSpace Obolon",
        location=Location(
            latitude=50.5018,
            longitude=30.4986,
            address="просп. Оболонський, 28, Київ"
        ),
        total_floors=2,
        rating=4.7,
        workspaces=[
            Workspace(
                id=801, coworking_id=3, floor=1, zone_type=ZoneType.OPEN_SPACE,
                name="Open Space 1-й поверх — Місце #5",
                description="Бюджетна зона для фрілансерів, безлімітна кава та чай",
                price_per_hour=35.0, price_per_day=200.0
            ),
            Workspace(
                id=901, coworking_id=3, floor=2, zone_type=ZoneType.SILENT_ZONE,
                name="Silent Zone 2-й поверх — Стіл #18",
                description="Тихе місце з видом на Оболонську набережну та окремим освітленням",
                price_per_hour=48.0, price_per_day=270.0
            ),
            Workspace(
                id=1001, coworking_id=3, floor=2, zone_type=ZoneType.MEETING_ROOM,
                name="Переговорна «Либідь»",
                description="Кімната на 6 осіб із TV, маркерною дошкою та кондиціонером",
                price_per_hour=160.0, price_per_day=950.0
            ),
        ]
    ),
]

