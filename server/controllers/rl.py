import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical

# PPO Model
class PPOModel(nn.Module):
    def __init__(self, input_size, output_size):
        super(PPOModel, self).__init__()
        self.actor = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.Tanh(),
            nn.Linear(64, 32),
            nn.Tanh(),
            nn.Linear(32, output_size),
            nn.Softmax(dim=-1)
        )
        self.critic = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.Tanh(),
            nn.Linear(64, 32),
            nn.Tanh(),
            nn.Linear(32, 1)
        )
        
    def forward(self, x):
        return self.actor(x), self.critic(x)

class PPOAgent:
    def __init__(self, team, state_dim=10, action_dim=4):
        self.team = team
        self.model = PPOModel(state_dim, action_dim)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.002)
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        
    def select_action(self, state):
        state = torch.FloatTensor(state).unsqueeze(0)
        action_probs, value = self.model(state)
        dist = Categorical(action_probs)
        action = dist.sample()
        
        self.states.append(state)
        self.actions.append(action)
        self.values.append(value)
        self.log_probs.append(dist.log_prob(action))
        
        return action.item()
    
    def update(self, next_value):
        returns = self.compute_returns(next_value)
        advantages = returns - torch.cat(self.values).detach()
        
        actor_loss = 0
        critic_loss = 0
        entropy = 0
        
        for log_prob, value, R, advantage in zip(self.log_probs, self.values, returns, advantages):
            advantage = advantage.detach()
            
            # Actor loss
            ratio = (log_prob - log_prob.detach()).exp()
            surr1 = ratio * advantage
            surr2 = torch.clamp(ratio, 0.8, 1.2) * advantage
            actor_loss -= torch.min(surr1, surr2).mean()
            
            # Critic loss
            critic_loss += 0.5 * (R - value).pow(2).mean()
            
            # Entropy (for exploration)
            entropy -= 0.01 * log_prob.mean()
        
        loss = actor_loss + critic_loss + entropy
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.values.clear()
        self.log_probs.clear()
    
    def compute_returns(self, next_value, gamma=0.99):
        R = next_value
        returns = []
        for step in reversed(range(len(self.rewards))):
            R = self.rewards[step] + gamma * R
            returns.insert(0, R)
        return torch.tensor(returns)