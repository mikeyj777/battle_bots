import numpy as np

from server.config.db import get_db_connection
from psycopg2.extras import RealDictCursor
from server.controllers.rl import PPOAgent

class Simulation:
    def __init__(self):
        self.reset()
        self.agent_models = {
            'A': PPOAgent('A'),
            'B': PPOAgent('B')
        }


    def get_simulation_state(self):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM bots")
        bots = cur.fetchall()
        
        cur.execute("SELECT * FROM weapons")
        weapons = cur.fetchall()
        
        cur.execute("SELECT * FROM barriers")
        barriers = cur.fetchall()
        
        cur.close()
        conn.close()

        return {
            'bots': bots,
            'weapons': weapons,
            'barriers': barriers
        }

    def update(self):

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM bots")
        bots = cur.fetchall()
        
        for bot in bots:
            state = self.get_state_near_bot(bot)
            action = self.agent_models[bot['team']].select_action(state)
            self.apply_action(bot, action)
            
            # Simple collision detection and health update
            cur.execute("SELECT * FROM weapons WHERE ABS(x - %s) < 5 AND ABS(y - %s) < 5", (bot['x'], bot['y']))
            collided_weapons = cur.fetchall()
            
            reward = 0
            for weapon in collided_weapons:
                bot['health'] -= weapon['strength']
                cur.execute("DELETE FROM weapons WHERE id = %s", (weapon['id'],))
                reward -= weapon['strength']  # Negative reward for taking damage
            
            bot['health'] = max(0, bot['health'])
            cur.execute("UPDATE bots SET health = %s WHERE id = %s", (bot['health'], bot['id']))
            
            # Additional reward for surviving and being close to enemies
            reward += 0.1  # Small positive reward for surviving
            if bot['health'] > 0:
                cur.execute("SELECT COUNT(*) FROM bots WHERE team != %s AND ((x - %s)^2 + (y - %s)^2) < 100", (bot['team'], bot['x'], bot['y']))
                nearby_enemies = cur.fetchone()[0]
                reward += nearby_enemies * 0.5  # Reward for being close to enemies
            
            self.agent_models[bot['team']].rewards.append(reward)
        
        # Update PPO agents
        for agent in self.agent_models.values():
            if agent.states:  # Only update if we have collected some experiences
                next_state = self.get_state_near_bot(bots[0])  # Use any bot's state as the next state
                _, next_value = agent.model(torch.FloatTensor(next_state).unsqueeze(0))
                agent.update(next_value)
        
        conn.commit()
        cur.close()
        conn.close()

    def reset(self):
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM bots")
        cur.execute("DELETE FROM weapons")
        cur.execute("DELETE FROM barriers")
        
        for i in range(10):
            cur.execute("INSERT INTO bots (team, x, y, health) VALUES (%s, %s, %s, %s)",
                        ('A' if i < 5 else 'B', np.random.rand()*300, np.random.rand()*300, 100))
        
        for _ in range(5):
            cur.execute("INSERT INTO weapons (x, y, strength) VALUES (%s, %s, %s)",
                        (np.random.rand()*300, np.random.rand()*300, 20))
        
        for _ in range(3):
            cur.execute("INSERT INTO barriers (x, y, width, height, durability) VALUES (%s, %s, %s, %s, %s)",
                        (np.random.rand()*250, np.random.rand()*250, 50, 20, 100))
        
        conn.commit()
        cur.close()
        conn.close()
    
    def get_state_near_bot(self, bot):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get nearby bots
        cur.execute("SELECT x, y FROM bots WHERE team != %s ORDER BY ((x - %s)^2 + (y - %s)^2) LIMIT 3", (bot['team'], bot['x'], bot['y']))
        nearby_bots = cur.fetchall()
        
        # Get nearby weapons
        cur.execute("SELECT x, y FROM weapons ORDER BY ((x - %s)^2 + (y - %s)^2) LIMIT 2", (bot['x'], bot['y']))
        nearby_weapons = cur.fetchall()
        
        cur.close()
        conn.close()
        
        state = [bot['x'], bot['y'], bot['health']]
        for nearby_bot in nearby_bots:
            state.extend([nearby_bot['x'], nearby_bot['y']])
        for weapon in nearby_weapons:
            state.extend([weapon['x'], weapon['y']])
        
        # Pad the state if we don't have enough nearby bots or weapons
        state.extend([0] * (10 - len(state)))
        
        return state

    def apply_action(self, bot, action):
        actions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # up, down, right, left
        dx, dy = actions[action]
        new_x = max(0, min(300, bot['x'] + dx * 5))
        new_y = max(0, min(300, bot['y'] + dy * 5))
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE bots SET x = %s, y = %s WHERE id = %s", (new_x, new_y, bot['id']))
        conn.commit()
        cur.close()
        conn.close()