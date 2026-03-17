import datetime

class T20WorldCup:
    def __init__(self, year, teams, matches):
        self.year = year
        self.teams = teams
        self.matches = matches

    def generate_review(self):
        review = f"T20 World Cup {self.year} Review:\n"
        review += f"Teams Participated: {', '.join(self.teams)}\n"
        review += f"Total Matches: {self.matches}\n"
        return review

    def create_posts(self):
        review = self.generate_review()
        linkedIn_post = f"Check out our complete review of the T20 World Cup {self.year}! \n{review} #T20WorldCup"
        twitter_post = f"T20 World Cup {self.year} Review: {review[:100]}... #T20WorldCup"
        return linkedIn_post, twitter_post

# Example Usage
if __name__ == '__main__':
    teams = ['India', 'Australia', 'England', 'Pakistan', 'South Africa', 'New Zealand']
    world_cup = T20WorldCup(2026, teams, 45)
    linkedIn_post, twitter_post = world_cup.create_posts()
    print(linkedIn_post)
    print(twitter_post)