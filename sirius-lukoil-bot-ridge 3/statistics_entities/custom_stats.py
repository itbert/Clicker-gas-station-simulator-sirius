from statistics_entities.user_stats import UserStatsVisitCount


# Сколько полных циклов подбора подарков запустил пользователь.
class UserStatsCyclesStartCount(UserStatsVisitCount):

    def __init__(self):
        super().__init__("CyclesStartsCount")


# Сколько полных циклов подбора подарков завершил пользователь
# (до момента получения сайта с подарками).
class UserStatsCyclesFinishCount(UserStatsVisitCount):

    def __init__(self):
        super().__init__("CyclesFinishCount")
