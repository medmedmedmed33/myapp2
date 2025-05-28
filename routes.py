from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Tournament, Team, Player, Match, MatchUpdate, MatchStats, PlayerStats, PlayerMatchPerformance
from forms import TournamentForm, TeamForm, PlayerForm, MatchForm, ScoreForm
from datetime import datetime, timedelta
import itertools
import random

@app.route('/')
def index():
    tournaments = Tournament.query.order_by(Tournament.created_at.desc()).limit(5).all()
    recent_matches = Match.query.filter_by(status='completed').order_by(Match.match_date.desc()).limit(5).all()
    return render_template('index.html', tournaments=tournaments, recent_matches=recent_matches)

# Tournament routes
@app.route('/tournaments')
def tournaments():
    tournaments = Tournament.query.order_by(Tournament.created_at.desc()).all()
    return render_template('tournaments/list.html', tournaments=tournaments)

@app.route('/tournaments/create', methods=['GET', 'POST'])
def create_tournament():
    form = TournamentForm()
    if form.validate_on_submit():
        tournament = Tournament(
            name=form.name.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            max_teams=form.max_teams.data
        )
        db.session.add(tournament)
        db.session.commit()
        flash(f'Tournament "{tournament.name}" created successfully!', 'success')
        return redirect(url_for('tournaments'))
    return render_template('tournaments/create.html', form=form)

@app.route('/tournaments/<int:id>')
def tournament_detail(id):
    tournament = Tournament.query.get_or_404(id)
    teams = Team.query.filter_by(tournament_id=id).all()
    matches = Match.query.filter_by(tournament_id=id).order_by(Match.match_date).all()
    
    # Calculate standings
    standings = []
    for team in teams:
        stats = team.get_stats()
        standings.append({
            'team': team,
            'stats': stats
        })
    
    # Sort standings by points, then goal difference, then goals for
    standings.sort(key=lambda x: (x['stats']['points'], x['stats']['goal_difference'], x['stats']['goals_for']), reverse=True)
    
    return render_template('tournaments/detail.html', tournament=tournament, teams=teams, matches=matches, standings=standings)

@app.route('/tournaments/<int:id>/generate_fixtures', methods=['POST'])
def generate_fixtures(id):
    tournament = Tournament.query.get_or_404(id)
    teams = Team.query.filter_by(tournament_id=id).all()
    
    if len(teams) < 2:
        flash('Need at least 2 teams to generate fixtures!', 'error')
        return redirect(url_for('tournament_detail', id=id))
    
    # Delete existing matches
    Match.query.filter_by(tournament_id=id).delete()
    
    # Generate round-robin fixtures
    team_combinations = list(itertools.combinations(teams, 2))
    start_date = tournament.start_date
    
    for i, (home_team, away_team) in enumerate(team_combinations):
        match_date = start_date + timedelta(days=i * 3)  # Matches every 3 days
        match = Match(
            tournament_id=id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            match_date=match_date,
            round_number=1
        )
        db.session.add(match)
    
    tournament.status = 'active'
    db.session.commit()
    flash('Fixtures generated successfully!', 'success')
    return redirect(url_for('tournament_detail', id=id))

# Team routes
@app.route('/teams')
def teams():
    teams = Team.query.order_by(Team.name).all()
    return render_template('teams/list.html', teams=teams)

@app.route('/tournaments/<int:tournament_id>/teams/create', methods=['GET', 'POST'])
def create_team(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    form = TeamForm()
    
    if form.validate_on_submit():
        # Check if tournament is full
        team_count = Team.query.filter_by(tournament_id=tournament_id).count()
        if team_count >= tournament.max_teams:
            flash('Tournament is full!', 'error')
            return redirect(url_for('tournament_detail', id=tournament_id))
        
        team = Team(
            name=form.name.data,
            city=form.city.data,
            founded_year=form.founded_year.data,
            coach=form.coach.data,
            tournament_id=tournament_id
        )
        db.session.add(team)
        db.session.commit()
        flash(f'Team "{team.name}" registered successfully!', 'success')
        return redirect(url_for('tournament_detail', id=tournament_id))
    
    return render_template('teams/create.html', form=form, tournament=tournament)

@app.route('/teams/<int:id>')
def team_detail(id):
    team = Team.query.get_or_404(id)
    players = Player.query.filter_by(team_id=id).order_by(Player.jersey_number).all()
    stats = team.get_stats()
    
    # Get player stats for the team
    players_with_stats = []
    for player in players:
        player_stats = player.get_stats()
        players_with_stats.append({
            'player': player,
            'stats': player_stats
        })
    
    return render_template('teams/detail.html', team=team, players=players_with_stats, stats=stats)

# Player routes
@app.route('/players')
def players():
    players = Player.query.join(Team).order_by(Team.name, Player.jersey_number).all()
    return render_template('players/list.html', players=players)

@app.route('/teams/<int:team_id>/players/create', methods=['GET', 'POST'])
def create_player(team_id):
    team = Team.query.get_or_404(team_id)
    form = PlayerForm()
    
    if form.validate_on_submit():
        # Check if jersey number is already taken
        existing_player = Player.query.filter_by(team_id=team_id, jersey_number=form.jersey_number.data).first()
        if existing_player:
            flash('Jersey number is already taken!', 'error')
            return render_template('players/create.html', form=form, team=team)
        
        player = Player(
            name=form.name.data,
            position=form.position.data,
            jersey_number=form.jersey_number.data,
            age=form.age.data,
            nationality=form.nationality.data,
            team_id=team_id
        )
        db.session.add(player)
        db.session.commit()
        flash(f'Player "{player.name}" added successfully!', 'success')
        return redirect(url_for('team_detail', id=team_id))
    
    return render_template('players/create.html', form=form, team=team)

# Match routes
@app.route('/matches')
def matches():
    matches = Match.query.order_by(Match.match_date.desc()).all()
    return render_template('matches/list.html', matches=matches)

@app.route('/matches/<int:id>/update_score', methods=['GET', 'POST'])
def update_score(id):
    match = Match.query.get_or_404(id)
    form = ScoreForm()
    
    if request.method == 'GET':
        form.home_score.data = match.home_score
        form.away_score.data = match.away_score
    
    if form.validate_on_submit():
        match.home_score = form.home_score.data
        match.away_score = form.away_score.data
        match.status = 'completed'
        db.session.commit()
        flash('Match score updated successfully!', 'success')
        return redirect(url_for('matches'))
    
    return render_template('matches/update_score.html', form=form, match=match)

@app.route('/tournaments/<int:id>/standings')
def standings(id):
    tournament = Tournament.query.get_or_404(id)
    teams = Team.query.filter_by(tournament_id=id).all()
    
    standings = []
    for team in teams:
        stats = team.get_stats()
        standings.append({
            'team': team,
            'stats': stats
        })
    
    # Sort standings by points, then goal difference, then goals for
    standings.sort(key=lambda x: (x['stats']['points'], x['stats']['goal_difference'], x['stats']['goals_for']), reverse=True)
    
    return render_template('standings.html', tournament=tournament, standings=standings)

# Live Match Routes
@app.route('/matches/<int:id>/live')
def live_match(id):
    match = Match.query.get_or_404(id)
    
    # Create match stats if they don't exist
    if not match.stats_detail:
        stats = MatchStats(match_id=id)
        db.session.add(stats)
        db.session.commit()
    
    return render_template('matches/live.html', match=match, home_team_players=match.home_team.players, away_team_players=match.away_team.players)

# API Routes for Live Updates
@app.route('/api/matches/<int:id>/live')
def api_live_match_data(id):
    match = Match.query.get_or_404(id)
    
    # Get recent updates (last 10)
    recent_updates = MatchUpdate.query.filter_by(match_id=id)\
                                    .order_by(MatchUpdate.timestamp.desc())\
                                    .limit(10).all()
    
    # Get match stats
    stats = match.stats_detail
    
    response_data = {
        'home_score': match.home_score,
        'away_score': match.away_score,
        'status': match.status,
        'updates': [update.to_dict() for update in recent_updates],
        'stats': stats.to_dict() if stats else None
    }
    
    return jsonify(response_data)

@app.route('/api/matches/<int:id>/score', methods=['POST'])
def api_update_score(id):
    match = Match.query.get_or_404(id)
    data = request.get_json()
    
    team = data.get('team')  # 'home' or 'away'
    
    if team == 'home':
        match.home_score += 1
        team_obj = Team.query.get(match.home_team_id)
    elif team == 'away':
        match.away_score += 1
        team_obj = Team.query.get(match.away_team_id)
    else:
        return jsonify({'error': 'Invalid team'}), 400
    
    # Create match update
    update = MatchUpdate(
        match_id=id,
        minute=random.randint(1, 90),
        update_type='goal',
        team_id=team_obj.id,
        description=f'⚽ BUT ! {team_obj.name} marque !'
    )
    
    # Update match stats
    if not match.stats_detail:
        stats = MatchStats(match_id=id)
        db.session.add(stats)
    else:
        stats = match.stats_detail
    
    # Simulate some stats updates
    if team == 'home':
        stats.home_shots += random.randint(1, 3)
        stats.home_shots_on_target += 1
    else:
        stats.away_shots += random.randint(1, 3)
        stats.away_shots_on_target += 1
    
    # Random possession adjustment
    possession_change = random.randint(-5, 5)
    if team == 'home':
        stats.home_possession = min(100, max(0, stats.home_possession + possession_change))
        stats.away_possession = 100 - stats.home_possession
    else:
        stats.away_possession = min(100, max(0, stats.away_possession + possession_change))
        stats.home_possession = 100 - stats.away_possession
    
    db.session.add(update)
    db.session.commit()
    
    return jsonify({
        'home_score': match.home_score,
        'away_score': match.away_score,
        'status': match.status,
        'stats': stats.to_dict(),
        'updates': [update.to_dict()]
    })

@app.route('/api/matches/<int:id>/start', methods=['POST'])
def api_start_match(id):
    match = Match.query.get_or_404(id)
    match.status = 'in_progress'
    
    # Create kick-off update
    update = MatchUpdate(
        match_id=id,
        minute=0,
        update_type='kickoff',
        description='🟢 Le match commence !'
    )
    
    db.session.add(update)
    db.session.commit()
    
    return jsonify({'status': 'success', 'match_status': match.status})

@app.route('/api/matches/<int:id>/end', methods=['POST'])
def api_end_match(id):
    match = Match.query.get_or_404(id)
    
    # Prevent processing if match is already completed
    if match.status == 'completed':
        return jsonify({'status': 'info', 'message': 'Match already completed.'}), 200

    # Set match status to completed
    match.status = 'completed'
    
    # Create final whistle update
    update = MatchUpdate(
        match_id=id,
        minute=90,
        update_type='final_whistle',
        description='🔴 Fin du match !'
    )
    db.session.add(update)

    # --- Suspension Logic --- #
    # 1. Lift suspensions for players whose suspension match was the just-completed one
    for team in [match.home_team, match.away_team]:
        for player in team.players:
            if player.is_suspended and player.suspended_until_match_id == match.id:
                player.is_suspended = False
                player.suspended_until_match_id = None
                flash(f'{player.name} is no longer suspended.', 'info') # Optional: notify users

    # 2. Process player performances from this match for new suspensions
    player_performances = PlayerMatchPerformance.query.filter_by(match_id=match.id).all()
    for performance in player_performances:
        player = performance.player
        player_stats = player.get_stats() # Get or create PlayerStats
        
        # Update cumulative stats with cards from this match
        player_stats.yellow_cards += performance.yellow_cards
        player_stats.red_cards += performance.red_cards
        player_stats.matches_played += 1 # Increment matches played
        player_stats.minutes_played += performance.minutes_played # Add minutes played
        player_stats.goals += performance.goals # Add goals
        player_stats.assists += performance.assists # Add assists
        # Add other stats updates as needed...

        db.session.add(player_stats)

        # Check for new suspensions (2 yellow cards OR 1 red card cumulative)
        if player_stats.yellow_cards >= 2 or player_stats.red_cards >= 1:
            if not player.is_suspended: # Avoid suspending someone already suspended
                player.is_suspended = True
                
                # Find the player's team's next scheduled match in the same tournament
                next_match = Match.query.filter(
                    db.or_(Match.home_team_id == player.team_id, Match.away_team_id == player.team_id),
                    Match.tournament_id == match.tournament_id, # Same tournament
                    Match.match_date > match.match_date, # After the current match date
                    Match.status == 'scheduled' # Must be a scheduled match
                ).order_by(Match.match_date.asc()).first()

                if next_match:
                    player.suspended_until_match_id = next_match.id
                    flash(f'{player.name} is suspended for the next match ({next_match.home_team.name} vs {next_match.away_team.name}).', 'warning') # Optional: notify users
                else:
                     # Handle case where there are no more scheduled matches for the team
                     # Player remains suspended until the end of the tournament/season
                     flash(f'{player.name} is suspended. No further matches scheduled for their team in this tournament.', 'warning')

        # Optional: Reset yellow card count after 2 yellows lead to suspension? (Depends on rules)
        # If accumulated yellow cards reset after a suspension:
        # if player_stats.yellow_cards >= 2:
        #    player_stats.yellow_cards = 0 # Reset yellow cards if they triggered a suspension
            

    db.session.commit()
    
    return jsonify({'status': 'success', 'match_status': match.status})

# API Route to record a player card
@app.route('/api/matches/<int:match_id>/player/<int:player_id>/card/<string:card_type>', methods=['POST'])
def api_record_card(match_id, player_id, card_type):
    match = Match.query.get_or_404(match_id)
    player = Player.query.get_or_404(player_id)

    # Ensure the player is in one of the teams playing the match
    if player.team_id != match.home_team_id and player.team_id != match.away_team_id:
        return jsonify({'error': 'Player is not in one of the teams playing this match.'}), 400

    # Find or create PlayerMatchPerformance entry for this player and match
    performance = PlayerMatchPerformance.query.filter_by(player_id=player_id, match_id=match_id).first()
    if not performance:
        # Create a minimal performance entry if it doesn't exist (e.g., if player came on as sub and wasn't selected initially)
        performance = PlayerMatchPerformance(player_id=player_id, match_id=match_id, is_selected=False, is_playing=True) # Assume playing if they get a card
        db.session.add(performance)

    # Update card count in performance
    if card_type == 'yellow':
        performance.yellow_cards += 1
        card_description = f'🟨 Carton jaune pour {player.name} ({player.team.name})'
    elif card_type == 'red':
        performance.red_cards += 1
        card_description = f'🟥 Carton rouge pour {player.name} ({player.team.name})'
    else:
        return jsonify({'error': 'Invalid card type.'}), 400

    # Create a MatchUpdate for the live feed
    # Get current match minute (can be approximated or added to API call)
    # For now, use a random minute for simulation
    current_minute = random.randint(1, 90)

    update = MatchUpdate(
        match_id=match_id,
        minute=current_minute,
        update_type='card',
        team_id=player.team_id,
        player_id=player_id,
        description=card_description
    )
    db.session.add(update)

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Card recorded for {player.name}.',
        'update': update.to_dict() # Return the update for the live feed
    })
