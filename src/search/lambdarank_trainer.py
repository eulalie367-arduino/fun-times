"""LambdaRank learning-to-rank optimization for search ranking."""

from typing import Dict, List, Tuple, Optional
import numpy as np
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RankingLabel:
    """Ranking label for training."""
    doc_id: str
    relevance: int  # 0-5 scale
    query_id: str
    signals: Dict[str, float]


class LambdaRankTrainer:
    """LambdaRank optimizer for learning-to-rank models."""

    def __init__(self, learning_rate: float = 0.1, lambda_weight: float = 1.0):
        """Initialize LambdaRank trainer.

        Args:
            learning_rate: Gradient descent learning rate
            lambda_weight: Lambda margin weight
        """
        self.learning_rate = learning_rate
        self.lambda_weight = lambda_weight
        self.weight_history: List[Dict] = []

    def compute_pairwise_loss(
        self,
        scores: np.ndarray,
        relevances: np.ndarray
    ) -> float:
        """Compute pairwise ranking loss.

        Args:
            scores: Predicted scores (n_docs,)
            relevances: Ground truth relevances (n_docs,)

        Returns:
            Pairwise loss value
        """
        loss = 0.0
        n = len(scores)

        for i in range(n):
            for j in range(i + 1, n):
                s_ij = scores[i] - scores[j]
                rel_ij = relevances[i] - relevances[j]

                if rel_ij > 0:
                    # Loss when i should rank higher than j
                    loss += 1.0 / (1.0 + np.exp(s_ij))

        return loss / (n * (n - 1) / 2)

    def compute_lambda_gradients(
        self,
        scores: np.ndarray,
        relevances: np.ndarray,
        features: np.ndarray
    ) -> np.ndarray:
        """Compute LambdaRank gradients.

        Args:
            scores: Predicted scores (n_docs,)
            relevances: Ground truth relevances (n_docs,)
            features: Feature vectors (n_docs, n_features)

        Returns:
            Gradients for each feature (n_features,)
        """
        gradients = np.zeros(features.shape[1])
        n = len(scores)

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue

                s_ij = scores[i] - scores[j]
                rel_ij = relevances[i] - relevances[j]

                if rel_ij != 0:
                    # Sigmoid probability of correct ranking
                    p_ij = 1.0 / (1.0 + np.exp(-s_ij))

                    # DCG change from swapping i and j
                    # Simplified: use relevance difference
                    dcg_delta = abs(rel_ij)

                    # Lambda gradient
                    lambda_grad = dcg_delta * (p_ij - (rel_ij > 0))
                    gradients += lambda_grad * (features[i] - features[j])

        return gradients / max(n - 1, 1)

    def train_step(
        self,
        weight_vector: np.ndarray,
        features_batch: List[np.ndarray],
        relevances_batch: List[np.ndarray]
    ) -> Tuple[np.ndarray, float]:
        """Single training step.

        Args:
            weight_vector: Current weight vector
            features_batch: Batch of feature matrices
            relevances_batch: Batch of relevance labels

        Returns:
            Updated weights and mean loss
        """
        total_loss = 0.0
        total_gradients = np.zeros_like(weight_vector)

        for features, relevances in zip(features_batch, relevances_batch):
            # Compute scores
            scores = features @ weight_vector

            # Compute loss
            loss = self.compute_pairwise_loss(scores, relevances)
            total_loss += loss

            # Compute gradients
            gradients = self.compute_lambda_gradients(scores, relevances, features)
            total_gradients += gradients

        # Update weights
        mean_gradients = total_gradients / len(features_batch)
        weight_vector -= self.learning_rate * mean_gradients

        return weight_vector, total_loss / len(features_batch)

    def train(
        self,
        training_data: List[Tuple[np.ndarray, np.ndarray]],
        initial_weights: Optional[np.ndarray] = None,
        epochs: int = 10,
        batch_size: int = 32
    ) -> Dict:
        """Full training procedure.

        Args:
            training_data: List of (features, relevances) pairs
            initial_weights: Initial weight vector
            epochs: Number of training epochs
            batch_size: Batch size for training

        Returns:
            Training results with final weights and loss history
        """
        if initial_weights is None:
            n_features = training_data[0][0].shape[1]
            weights = np.ones(n_features) / n_features
        else:
            weights = initial_weights.copy()

        loss_history = []

        for epoch in range(epochs):
            epoch_loss = 0.0
            n_batches = 0

            for i in range(0, len(training_data), batch_size):
                batch = training_data[i:i + batch_size]
                features_batch = [x[0] for x in batch]
                relevances_batch = [x[1] for x in batch]

                weights, batch_loss = self.train_step(
                    weights,
                    features_batch,
                    relevances_batch
                )

                epoch_loss += batch_loss
                n_batches += 1

            mean_loss = epoch_loss / max(n_batches, 1)
            loss_history.append(mean_loss)

            logger.info(f"Epoch {epoch + 1}/{epochs} - Loss: {mean_loss:.6f}")

        self.weight_history.append({
            'weights': weights.copy(),
            'loss_history': loss_history
        })

        return {
            'final_weights': weights,
            'loss_history': loss_history,
            'final_loss': loss_history[-1] if loss_history else float('inf')
        }


class OnlineLTRUpdater:
    """Online learning-to-rank weight updates."""

    def __init__(self, initial_weights: Dict[str, float]):
        """Initialize online updater.

        Args:
            initial_weights: Initial signal weights
        """
        self.weights = initial_weights.copy()
        self.update_count = 0

    def update_from_click(
        self,
        query: str,
        clicked_rank: int,
        ranking_scores: Dict[str, float]
    ) -> None:
        """Update weights from user click.

        Args:
            query: Query string
            clicked_rank: Rank position of clicked result
            ranking_scores: Dictionary of signal scores
        """
        # Implicit relevance: clicked result preferred
        # Adjust weights slightly towards signals that scored clicked result higher
        if clicked_rank > 0:
            # Discount: lower rank gets smaller weight change
            discount = 1.0 / np.log2(clicked_rank + 2)

            for signal_name, score in ranking_scores.items():
                if signal_name in self.weights:
                    # Small adjustment towards clicked result
                    self.weights[signal_name] += 0.01 * discount * score

        self.update_count += 1

    def update_from_impression(
        self,
        ranking_scores: List[Dict[str, float]],
        relevant_positions: List[int]
    ) -> None:
        """Update weights from search impressions.

        Args:
            ranking_scores: List of signal dicts for each result
            relevant_positions: Positions of relevant results
        """
        relevant_set = set(relevant_positions)

        for rank, scores in enumerate(ranking_scores):
            is_relevant = rank in relevant_set

            for signal_name, score in scores.items():
                if signal_name in self.weights:
                    if is_relevant:
                        self.weights[signal_name] += 0.005 * score
                    else:
                        self.weights[signal_name] -= 0.002 * score

        # Normalize weights
        total = sum(abs(w) for w in self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

        self.update_count += 1

    def get_weights(self) -> Dict[str, float]:
        """Get current weights."""
        return self.weights.copy()

    def get_update_stats(self) -> Dict:
        """Get update statistics."""
        return {
            'total_updates': self.update_count,
            'current_weights': self.weights.copy()
        }
