from collections import OrderedDict
import logging
from src.core.redis_service import cached
from src.apis.clash_of_clans.services.clashking_service import ClashKingClient
import config


class PlayerEssentialsService:
    """Service for processing essential player data for mobile app"""

    def __init__(self):
        # Initialize ClashKing client
        self.clashking_client = ClashKingClient()

        # Define ordering for all game elements
        self.hero_order = ['Barbarian King', 'Archer Queen', 'Minion Prince', 'Grand Warden', 'Royal Champion']

        self.pet_order = ['L.A.S.S.I', 'Electro Owl', 'Mighty Yak', 'Unicorn', 'Frosty', 'Diggy',
                          'Poison Lizard', 'Phoenix', 'Spirit Fox', 'Angry Jelly', 'Sneezy']

        self.elixir_troops_order = ['Barbarian', 'Archer', 'Giant', 'Goblin', 'Wall Breaker', 'Balloon',
                                    'Wizard', 'Healer', 'Dragon', 'P.E.K.K.A', 'Baby Dragon', 'Miner',
                                    'Electro Dragon', 'Electro Titan', 'Yeti', 'Dragon Rider', 'Root Rider', 'Thrower']

        self.dark_elixir_troops_order = ['Minion', 'Hog Rider', 'Valkyrie', 'Golem', 'Witch', 'Lava Hound',
                                         'Bowler', 'Ice Golem', 'Headhunter', 'Apprentice Warden', 'Druid', 'Furnace']

        self.siege_machines_order = ['Wall Wrecker', 'Battle Blimp', 'Stone Slammer', 'Siege Barracks',
                                     'Log Launcher', 'Flame Flinger', 'Battle Drill', 'Troop Launcher']

        self.elixir_spells_order = ['Lightning Spell', 'Healing Spell', 'Rage Spell', 'Jump Spell',
                                    'Freeze Spell', 'Clone Spell', 'Invisibility Spell', 'Recall Spell', 'Revive Spell']

        self.dark_elixir_spells_order = ['Poison Spell', 'Earthquake Spell', 'Haste Spell', 'Skeleton Spell',
                                         'Bat Spell', 'Overgrowth Spell', 'Ice Block Spell']

        self.hero_equipment_order = {
            'Barbarian King': ['Barbarian Puppet', 'Rage Vial', 'Earthquake Boots', 'Vampstache',
                               'Giant Gauntlet', 'Snake Bracelet', 'Spiky Ball'],
            'Archer Queen': ['Archer Puppet', 'Invisibility Vial', 'Giant Arrow', 'Healer Puppet',
                             'Action Figure', 'Frozen Arrow', 'Magic Mirror'],
            'Minion Prince': ['Dark Orb', 'Henchmen Puppet', 'Metal Pants', 'Noble Iron', 'Dark Crown'],
            'Grand Warden': ['Eternal Tome', 'Life Gem', 'Healing Tome', 'Rage Gem',
                             'Lavaloon Puppet', 'Fireball'],
            'Royal Champion': ['Royal Gem', 'Seeking Shield', 'Haste Vial', 'Hog Rider Puppet',
                               'Electro Boots', 'Rocket Spear']
        }

        # Epic equipment mapping
        self.epic_equipment = {
            'Giant Gauntlet', 'Snake Bracelet', 'Spiky Ball',  # Barbarian King
            'Action Figure', 'Frozen Arrow', 'Magic Mirror',  # Archer Queen
            'Dark Crown',  # Minion Prince
            'Lavaloon Puppet', 'Fireball',  # Grand Warden
            'Electro Boots', 'Rocket Spear'  # Royal Champion
        }

    @cached(timeout=300)  # Cache for 5 minutes
    def format_player_essentials(self, player_data):
        """
        Extract and format essential player data for mobile app

        Args:
            player_data: Raw player data from Clash of Clans API

        Returns:
            OrderedDict: Formatted essential player data
        """
        # Extract basic player info
        player_name = player_data.get('name', 'Unknown')
        player_tag = player_data.get('tag', '')

        # Extract clan info
        clan_info = {}
        if 'clan' in player_data:
            clan_info = {
                'name': player_data['clan'].get('name', ''),
                'tag': player_data['clan'].get('tag', ''),
                'badgeUrls': player_data['clan'].get('badgeUrls', {}),
                'clanLevel': player_data['clan'].get('clanLevel', 0)
            }

        # Extract league info
        league_info = {}
        if 'league' in player_data:
            league_info = {
                'name': player_data['league'].get('name', '')
            }

        # Extract legends ranking from ClashKing API
        legends_info = self._get_legends_ranking(player_tag, player_data)

        # Get highest trophy from achievements
        highest_trophy = self._get_highest_trophy(player_data.get('achievements', []))

        # Build result in specified order
        result = OrderedDict([
            ('clan', clan_info),
            ('clanCapitalContributions', player_data.get('clanCapitalContributions', 0)),
            ('defenseWins', player_data.get('defenseWins', 0)),
            ('donations', player_data.get('donations', 0)),
            ('donationsReceived', player_data.get('donationsReceived', 0)),
            ('expLevel', player_data.get('expLevel', 0)),
            ('league', league_info),
            ('role', player_data.get('role', '')),
            ('achievements', highest_trophy),
            ('legends', legends_info),  # Add legends ranking here
            ('trophies', player_data.get('trophies', 0)),
            ('warPreference', player_data.get('warPreference', '')),
            ('warStars', player_data.get('warStars', 0)),
            ('townHallLevel', player_data.get('townHallLevel', 0)),
            ('heroes', self._format_heroes(player_data.get('heroes', []))),
            ('heroEquipment', self._format_hero_equipment(player_data)),
            ('pets', self._format_pets(player_data.get('troops', []))),
            ('elixirTroops', self._format_elixir_troops(player_data.get('troops', []))),
            ('darkElixirTroops', self._format_dark_elixir_troops(player_data.get('troops', []))),
            ('siegeMachines', self._format_siege_machines(player_data.get('troops', []))),
            ('elixirSpells', self._format_elixir_spells(player_data.get('spells', []))),
            ('darkElixirSpells', self._format_dark_elixir_spells(player_data.get('spells', []))),
            ('playerName', player_name),
            ('playerTag', player_tag)
        ])

        return result

    def _get_legends_ranking(self, player_tag, player_data):
        """Get legends ranking from ClashKing API with fallback to COC API"""
        try:
            # Get combined legends data from ClashKing API (global + local + seasons)
            clashking_legends = self.clashking_client.get_combined_legends_data(player_tag)
            if clashking_legends and (clashking_legends.get('global_rank') is not None or clashking_legends.get(
                    'local_rank') is not None):
                logging.info(f"Successfully retrieved legends data from ClashKing for {player_tag}")
                return clashking_legends

        except Exception as e:
            logging.warning(f"ClashKing API failed for {player_tag}: {str(e)}")

        # Fallback to COC API legends data if available
        legends_data = player_data.get('legends', {})
        if legends_data:
            logging.info(f"Using legends data from COC API for {player_tag}")
            return {
                'global_rank': legends_data.get('global_rank'),
                'local_rank': legends_data.get('local_rank'),
                'previous_season': legends_data.get('previousSeason'),
                'best_season': legends_data.get('bestSeason')
            }

        # No legends data available
        logging.info(f"No legends data available for {player_tag}")
        return {}

    def _get_highest_trophy(self, achievements):
        """Extract highest trophy value from achievements"""
        for achievement in achievements:
            if achievement.get('name') == 'Sweet Victory!':
                return {
                    'completionInfo': achievement.get('completionInfo', ''),
                    'info': achievement.get('info', ''),
                    'name': achievement.get('name', ''),
                    'stars': achievement.get('stars', 0),
                    'target': achievement.get('target', 0),
                    'value': achievement.get('value', 0),
                    'village': achievement.get('village', 'home')
                }
        return {}

    def _format_heroes(self, heroes):
        """Format heroes data in specified order"""
        formatted_heroes = []
        hero_order_mapping = {hero: idx for idx, hero in enumerate(self.hero_order)}

        # Sort heroes by the specified order
        sorted_heroes = sorted(heroes, key=lambda h: hero_order_mapping.get(h.get('name', ''), 999))

        for hero in sorted_heroes:
            if hero.get('village', 'home') == 'home' and hero.get('name') in self.hero_order:
                formatted_hero = {
                    'name': hero.get('name', ''),
                    'level': hero.get('level', 0),
                    'maxLevel': hero.get('maxLevel', 0),
                    'village': hero.get('village', 'home'),
                    'order': hero_order_mapping.get(hero.get('name', ''), 0)
                }
                formatted_heroes.append(formatted_hero)

        return formatted_heroes

    def _format_hero_equipment(self, player_data):
        """Format hero equipment data in specified order"""
        equipment_by_hero = OrderedDict()

        # Get heroes and global equipment data
        heroes = player_data.get('heroes', [])
        all_hero_equipment = player_data.get('heroEquipment', [])

        # Create a mapping of all equipment the player owns with their levels
        player_equipment_levels = {}
        for equipment in all_hero_equipment:
            equipment_name = equipment.get('name', '')
            player_equipment_levels[equipment_name] = {
                'level': equipment.get('level', 0),
                'maxLevel': equipment.get('maxLevel', 0)
            }

        # Define proper camelCase hero keys in the specified order
        hero_keys = ['barbarianKing', 'archerQueen', 'minionPrince', 'grandWarden', 'royalChampion']

        for hero_key in hero_keys:
            # Convert camelCase to proper hero name
            hero_name = hero_key.replace('barbarianKing', 'Barbarian King') \
                .replace('archerQueen', 'Archer Queen') \
                .replace('minionPrince', 'Minion Prince') \
                .replace('grandWarden', 'Grand Warden') \
                .replace('royalChampion', 'Royal Champion')

            equipment_by_hero[hero_key] = []

            # Find the hero in the data
            hero_data = None
            for hero in heroes:
                if hero.get('name') == hero_name and hero.get('village', 'home') == 'home':
                    hero_data = hero
                    break

            # Get equipped equipment (only equipment that appears in the hero's equipment list)
            equipped_equipment = set()
            if hero_data:
                equipped_equipment_list = hero_data.get('equipment', [])
                for eq in equipped_equipment_list:
                    equipped_equipment.add(eq.get('name'))

            # Process all equipment for this hero in specified order
            equipment_order = self.hero_equipment_order.get(hero_name, [])

            for idx, equipment_name in enumerate(equipment_order):
                is_epic = equipment_name in self.epic_equipment
                is_equipped = equipment_name in equipped_equipment

                # Get the actual level from the global heroEquipment array
                if equipment_name in player_equipment_levels:
                    level = player_equipment_levels[equipment_name]['level']
                    max_level = player_equipment_levels[equipment_name]['maxLevel']
                else:
                    # Player doesn't own this equipment
                    level = 0
                    max_level = 27 if is_epic else 18

                equipment_item = {
                    'name': equipment_name,
                    'level': level,
                    'maxLevel': max_level,
                    'village': 'home',
                    'isEpic': is_epic,
                    'isEquipped': is_equipped,
                    'order': idx  # Order based on position in the predefined list (0-indexed)
                }

                equipment_by_hero[hero_key].append(equipment_item)

        return equipment_by_hero

    def _format_pets(self, troops):
        """Format pets data in specified order"""
        pets = []
        pet_order_mapping = {pet: idx for idx, pet in enumerate(self.pet_order)}

        for troop in troops:
            if troop.get('name') in self.pet_order:
                formatted_pet = {
                    'name': troop.get('name', ''),
                    'level': troop.get('level', 0),
                    'maxLevel': troop.get('maxLevel', 0),
                    'village': troop.get('village', 'home'),
                    'order': pet_order_mapping.get(troop.get('name', ''), 0)
                }
                pets.append(formatted_pet)

        return sorted(pets, key=lambda p: p['order'])

    def _format_elixir_troops(self, troops):
        """Format elixir troops data in specified order"""
        elixir_troops = []
        troop_order_mapping = {troop: idx for idx, troop in enumerate(self.elixir_troops_order)}

        for troop in troops:
            if troop.get('name') in self.elixir_troops_order:
                formatted_troop = {
                    'name': troop.get('name', ''),
                    'level': troop.get('level', 0),
                    'maxLevel': troop.get('maxLevel', 0),
                    'village': troop.get('village', 'home'),
                    'order': troop_order_mapping.get(troop.get('name', ''), 0)
                }
                elixir_troops.append(formatted_troop)

        return sorted(elixir_troops, key=lambda t: t['order'])

    def _format_dark_elixir_troops(self, troops):
        """Format dark elixir troops data in specified order"""
        dark_troops = []
        troop_order_mapping = {troop: idx for idx, troop in enumerate(self.dark_elixir_troops_order)}

        for troop in troops:
            if troop.get('name') in self.dark_elixir_troops_order:
                formatted_troop = {
                    'name': troop.get('name', ''),
                    'level': troop.get('level', 0),
                    'maxLevel': troop.get('maxLevel', 0),
                    'village': troop.get('village', 'home'),
                    'order': troop_order_mapping.get(troop.get('name', ''), 0)
                }
                dark_troops.append(formatted_troop)

        return sorted(dark_troops, key=lambda t: t['order'])

    def _format_siege_machines(self, troops):
        """Format siege machines data in specified order"""
        siege_machines = []
        siege_order_mapping = {siege: idx for idx, siege in enumerate(self.siege_machines_order)}

        for troop in troops:
            if troop.get('name') in self.siege_machines_order:
                formatted_siege = {
                    'name': troop.get('name', ''),
                    'level': troop.get('level', 0),
                    'maxLevel': troop.get('maxLevel', 0),
                    'village': troop.get('village', 'home'),
                    'order': siege_order_mapping.get(troop.get('name', ''), 0)
                }
                siege_machines.append(formatted_siege)

        return sorted(siege_machines, key=lambda s: s['order'])

    def _format_elixir_spells(self, spells):
        """Format elixir spells data in specified order"""
        elixir_spells = []
        spell_order_mapping = {spell: idx for idx, spell in enumerate(self.elixir_spells_order)}

        for spell in spells:
            if spell.get('name') in self.elixir_spells_order:
                formatted_spell = {
                    'name': spell.get('name', ''),
                    'level': spell.get('level', 0),
                    'maxLevel': spell.get('maxLevel', 0),
                    'village': spell.get('village', 'home'),
                    'order': spell_order_mapping.get(spell.get('name', ''), 0)
                }
                elixir_spells.append(formatted_spell)

        return sorted(elixir_spells, key=lambda s: s['order'])

    def _format_dark_elixir_spells(self, spells):
        """Format dark elixir spells data in specified order"""
        dark_spells = []
        spell_order_mapping = {spell: idx for idx, spell in enumerate(self.dark_elixir_spells_order)}

        for spell in spells:
            if spell.get('name') in self.dark_elixir_spells_order:
                formatted_spell = {
                    'name': spell.get('name', ''),
                    'level': spell.get('level', 0),
                    'maxLevel': spell.get('maxLevel', 0),
                    'village': spell.get('village', 'home'),
                    'order': spell_order_mapping.get(spell.get('name', ''), 0)
                }
                dark_spells.append(formatted_spell)

        return sorted(dark_spells, key=lambda s: s['order'])