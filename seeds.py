from app import app
from extensions import db
from models import User, Admin, Coach, Referee, Tournament, Team, Player, Match
from werkzeug.security import generate_password_hash
from datetime import datetime, date
import random
import string

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def seed_users():
    print("Seeding users...")
    # Check if admin already exists to avoid creating duplicates
    if not Admin.query.first():
        admin_user = Admin(
            username='admin',
            email='admin@example.com',
            first_name='Super',
            last_name='Admin',
            role='admin'
        )
        admin_user.set_password('adminpassword') # TODO: Use a stronger password in production
        db.session.add(admin_user)
        print(" - Created Admin user")

    # Create enough coaches for 16 teams + some extra
    coaches_data = [
        {'first_name': 'Walid', 'last_name': 'Regragui', 'email': 'walid.regragui@example.com'},
        {'first_name': 'Jamal', 'last_name': 'Sellami', 'email': 'jamal.sellami@example.com'},
        {'first_name': 'Faouzi', 'last_name': 'Benzarti', 'email': 'faouzi.benzarti@example.com'},
        {'first_name': 'Rachid', 'last_name': 'Taoussi', 'email': 'rachid.taoussi@example.com'},
        {'first_name': 'Hussein', 'last_name': 'Amouta', 'email': 'hussein.amouta@example.com'},
        {'first_name': 'Abdelkader', 'last_name': 'Amrane', 'email': 'abdelkader.amrane@example.com'},
        {'first_name': 'Hassan', 'last_name': 'Moumen', 'email': 'hassan.moumen@example.com'},
        {'first_name': 'Ezzaki', 'last_name': 'Badou', 'email': 'ezzaki.badou@example.com'},
        {'first_name': 'Mustapha', 'last_name': 'Hadji', 'email': 'mustapha.hadji@example.com'},
        {'first_name': 'Mohamed', 'last_name': 'Fakhir', 'email': 'mohamed.fakhir@example.com'},
        {'first_name': 'Khalid', 'last_name': 'Foqra', 'email': 'khalid.foqra@example.com'},
        {'first_name': 'Aziz', 'last_name': 'Amri', 'email': 'aziz.amri@example.com'},
        {'first_name': 'Younes', 'last_name': 'Ali', 'email': 'younes.ali@example.com'},
        {'first_name': 'Tarek', 'last_name': 'Sektioui', 'email': 'tarek.sektioui@example.com'},
        {'first_name': 'Bernard', 'last_name': 'Casoni', 'email': 'bernard.casoni@example.com'}, # Example foreign coach
        {'first_name': 'Patrice', 'last_name': 'Carteron', 'email': 'patrice.carteron@example.com'}, # Example foreign coach
        {'first_name': 'Juan Carlos', 'last_name': 'Garrido', 'email': 'juan.carlos@example.com'}, # Example foreign coach
        {'first_name': 'Sébastien', 'last_name': 'Desabre', 'email': 'sebastien.desabre@example.com'}, # Example foreign coach

    ]

    for coach_data in coaches_data:
        if not User.query.filter_by(email=coach_data['email']).first():
            username_base = f"{coach_data['first_name'][0]}{coach_data['last_name']}".lower()
            # Ensure username is somewhat unique, append random digits
            username = f"{username_base}{random.randint(10, 999)}"
            password = generate_random_password()
            coach_user = Coach(
                username=username,
                email=coach_data['email'],
                first_name=coach_data['first_name'],
                last_name=coach_data['last_name'],
                role='coach'
            )
            coach_user.set_password(password)
            db.session.add(coach_user)
            print(f" - Created Coach: {coach_user.username} with password {password}")

    # Create some referees
    referees_data = [
        {'first_name': 'Redouane', 'last_name': 'Jiyed', 'email': 'redouane.jiyed@example.com', 'nationality': 'Moroccan'},
        {'first_name': 'Samir', 'last_name': 'Guezzaz', 'email': 'samir.guezzaz@example.com', 'nationality': 'Moroccan'},
        {'first_name': 'Noureddine', 'last_name': 'El Jaafari', 'email': 'noureddine.eljaafari@example.com', 'nationality': 'Moroccan'},
        {'first_name': 'Bouchaib', 'last_name': 'El Ahrach', 'email': 'bouchaib.elahrach@example.com', 'nationality': 'Moroccan'},
    ]

    for referee_data in referees_data:
        if not User.query.filter_by(email=referee_data['email']).first():
             username_base = f"{referee_data['first_name'][0]}{referee_data['last_name']}".lower()
             # Ensure username is somewhat unique, append random digits
             username = f"{username_base}{random.randint(10, 999)}"
             password = generate_random_password()
             referee_user = Referee(
                 username=username,
                 email=referee_data['email'],
                 first_name=referee_data['first_name'],
                 last_name=referee_data['last_name'],
                 role='referee',
                 nationality=referee_data['nationality']
             )
             referee_user.set_password(password)
             db.session.add(referee_user)
             print(f" - Created Referee: {referee_user.username} with password {password}")

    db.session.commit()
    print("Users seeding complete.")

def seed_tournaments():
    print("Seeding tournaments...")
    # Define the tournament name
    tournament_name = 'Botola Pro 1'
    tournament = Tournament.query.filter_by(name=tournament_name).first()

    if not tournament:
        tournament = Tournament(
            name=tournament_name,
            description='Top tier Moroccan football league',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 15),
            max_teams=16, # Ensure max_teams is at least 16
            status='registration'
        )
        db.session.add(tournament)
        db.session.commit()
        print(f" - Created Tournament: {tournament_name}")
    else:
        print(f"Tournament '{tournament.name}' already exists.")
        # Update max_teams if it's less than 16
        if tournament.max_teams < 16:
             tournament.max_teams = 16
             db.session.commit()
             print(f" - Updated '{tournament.name}' max_teams to 16.")


    print("Tournaments seeding complete.")
    return tournament

def seed_teams(tournament):
    print("Seeding teams...")
    teams_data = [
        {'name': 'Raja Club Athletic', 'city': 'Casablanca', 'founded_year': 1949},
        {'name': 'Wydad Athletic Club', 'city': 'Casablanca', 'founded_year': 1937},
        {'name': 'AS FAR', 'city': 'Rabat', 'founded_year': 1958},
        {'name': 'RS Berkane', 'city': 'Berkane', 'founded_year': 1958},
        {'name': 'FUS Rabat', 'city': 'Rabat', 'founded_year': 1946},
        {'name': 'Mouloudia Oujda', 'city': 'Oujda', 'founded_year': 1946},
        {'name': 'Hassania Agadir', 'city': 'Agadir', 'founded_year': 1946},
        {'name': 'Ittihad Tanger', 'city': 'Tangier', 'founded_year': 1936},
        {'name': 'Maghreb de Fès', 'city': 'Fes', 'founded_year': 1946},
        {'name': 'Olympique Khouribga', 'city': 'Khouribga', 'founded_year': 1923},
        {'name': 'Rapide Oued Zem', 'city': 'Oued Zem', 'founded_year': 1983},
        {'name': 'Youssoufia Berrechid', 'city': 'Berrechid', 'founded_year': 1957},
        {'name': 'Renaissance Zemamra', 'city': 'Zemamra', 'founded_year': 2009},
        {'name': 'Jeunesse Sportive Soualem', 'city': 'Soualem', 'founded_year': 2004},
        {'name': 'Union Touarga Sport', 'city': 'Rabat', 'founded_year': 1971},
        {'name': 'Difaâ Hassani El Jadidi', 'city': 'El Jadida', 'founded_year': 1956},
    ]

    coaches = Coach.query.all()
    # Shuffle coaches to assign them randomly
    random.shuffle(coaches)
    coach_index = 0
    created_teams_count = 0

    for team_data in teams_data:
        # Stop creating teams if we reach max_teams for the tournament
        if created_teams_count >= tournament.max_teams:
            print(f"Max teams ({tournament.max_teams}) reached for tournament. Stopping team seeding.")
            break

        team = Team.query.filter_by(name=team_data['name'], tournament_id=tournament.id).first()
        if not team:
            team = Team(
                name=team_data['name'],
                city=team_data['city'],
                founded_year=team_data['founded_year'],
                tournament_id=tournament.id
            )

            # Assign a coach if available
            if coach_index < len(coaches):
                team.coach = coaches[coach_index]
                print(f" - Assigned coach {coaches[coach_index].username} to {team.name}")
                coach_index += 1
            else:
                 print(f" - Warning: No more coaches available to assign to {team.name}")

            db.session.add(team)
            print(f" - Created Team: {team.name}")
            created_teams_count += 1
        else:
             print(f" - Team '{team.name}' already exists.")


    db.session.commit()
    print("Teams seeding complete.")

def seed_players(teams):
    print("Seeding players...")
    positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
    nationalities = ['Moroccan', 'Senegalese', 'Ivorian', 'Cameroonian', 'Nigerian'] # Sample nationalities

    for team in teams:
        # Check how many players the team currently has
        current_players_count = len(team.players)
        players_to_add = 20 - current_players_count

        if players_to_add > 0:
            print(f" - Adding {players_to_add} players to {team.name}...")
            for i in range(players_to_add):
                # Generate a simple player name (e.g., PlayerX)
                player_name = f"Player {i + current_players_count + 1} ({team.name})" # Make name somewhat unique
                position = random.choice(positions)
                jersey_number = random.randint(1, 99)
                age = random.randint(17, 38)
                nationality = random.choice(nationalities)

                player = Player(
                    name=player_name,
                    position=position,
                    jersey_number=jersey_number,
                    age=age,
                    nationality=nationality,
                    team_id=team.id
                )
                db.session.add(player)
                # print(f"   - Added player {player.name}") # Uncomment for detailed player creation logs

    db.session.commit()
    print("Players seeding complete.")

def seed_matches(tournament, teams):
    print("Seeding matches...")
    # Simple example: create matches between pairs of teams
    # This is a basic seeding, a real league schedule is more complex
    existing_matches_count = len(tournament.matches)
    if existing_matches_count == 0 and len(teams) >= 2:
        print(" - Creating example matches...")
        # Create matches for the first few pairs of teams
        for i in range(0, len(teams) - 1, 2):
             if i + 1 < len(teams):
                 home_team = teams[i]
                 away_team = teams[i+1]
                 match_date = datetime(2024, 9, 15 + i, 18, 0, 0) # Example dates
                 venue = f'Stadium of {home_team.city}' # Example venue

                 match = Match(
                     tournament_id=tournament.id,
                     home_team_id=home_team.id,
                     away_team_id=away_team.id,
                     match_date=match_date,
                     venue=venue,
                     round_number=1
                 )
                 db.session.add(match)
                 print(f"   - Created match: {home_team.name} vs {away_team.name} on {match_date.strftime('%Y-%m-%d')}")

        db.session.commit()
    else:
        print(" - Matches already exist or not enough teams to create pairs.")

    print("Matches seeding complete.")


if __name__ == '__main__':
    with app.app_context():
        print("Starting database seeding...")
        # Create database tables if they don't exist
        db.create_all()

        seed_users()
        tournament = seed_tournaments()
        # Only seed teams and players if a tournament was created or found
        if tournament:
            # Fetch teams after potential initial creation
            teams = Team.query.filter_by(tournament_id=tournament.id).all()

            # Seed teams if the current number is less than max_teams
            if len(teams) < tournament.max_teams:
                 seed_teams(tournament)
                 # Refresh teams list after seeding
                 teams = Team.query.filter_by(tournament_id=tournament.id).all()

            # Seed players for all teams in the tournament
            if teams:
                 seed_players(teams)

            # Seed matches for the tournament
            seed_matches(tournament, teams)

        print("Database seeding complete.") 