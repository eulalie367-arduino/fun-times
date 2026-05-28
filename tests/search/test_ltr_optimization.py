"""Tests for LambdaRank learning-to-rank optimization."""

import numpy as np
import pytest
from src.search.lambdarank_trainer import LambdaRankTrainer, OnlineLTRUpdater


class TestLambdaRankTrainer:
    """Test LambdaRank trainer."""

    def test_initialization(self):
        """Test trainer initialization."""
        trainer = LambdaRankTrainer(learning_rate=0.1)
        assert trainer.learning_rate == 0.1

    def test_pairwise_loss(self):
        """Test pairwise loss computation."""
        trainer = LambdaRankTrainer()
        scores = np.array([0.8, 0.6, 0.4])
        relevances = np.array([2, 1, 0])

        loss = trainer.compute_pairwise_loss(scores, relevances)
        assert 0 <= loss <= 1

    def test_lambda_gradients(self):
        """Test gradient computation."""
        trainer = LambdaRankTrainer()
        scores = np.array([0.8, 0.6, 0.4])
        relevances = np.array([2, 1, 0])
        features = np.random.randn(3, 5)

        gradients = trainer.compute_lambda_gradients(scores, relevances, features)
        assert gradients.shape == (5,)

    def test_train_step(self):
        """Test single training step."""
        trainer = LambdaRankTrainer()
        weights = np.ones(5) / 5
        features = np.random.randn(3, 5)
        relevances = np.array([2, 1, 0])

        new_weights, loss = trainer.train_step(
            weights,
            [features],
            [relevances]
        )

        assert new_weights.shape == weights.shape
        assert 0 <= loss <= 1

    def test_training(self):
        """Test full training."""
        trainer = LambdaRankTrainer(learning_rate=0.01)

        # Create training data
        training_data = []
        for _ in range(10):
            features = np.random.randn(4, 4)
            relevances = np.array([2, 1, 1, 0])
            training_data.append((features, relevances))

        results = trainer.train(training_data, epochs=3)

        assert 'final_weights' in results
        assert 'loss_history' in results
        assert len(results['loss_history']) == 3


class TestOnlineLTRUpdater:
    """Test online LTR weight updates."""

    def test_initialization(self):
        """Test updater initialization."""
        weights = {'bm25': 0.4, 'recency': 0.2, 'popularity': 0.4}
        updater = OnlineLTRUpdater(weights)
        assert updater.update_count == 0

    def test_click_update(self):
        """Test update from click."""
        weights = {'bm25': 0.4, 'recency': 0.3, 'popularity': 0.3}
        updater = OnlineLTRUpdater(weights)

        ranking_scores = {'bm25': 0.8, 'recency': 0.5, 'popularity': 0.9}
        updater.update_from_click("test query", 2, ranking_scores)

        assert updater.update_count == 1
        new_weights = updater.get_weights()
        assert 'bm25' in new_weights

    def test_impression_update(self):
        """Test update from impressions."""
        weights = {'bm25': 0.4, 'recency': 0.3, 'popularity': 0.3}
        updater = OnlineLTRUpdater(weights)

        ranking_scores = [
            {'bm25': 0.8, 'recency': 0.5, 'popularity': 0.9},
            {'bm25': 0.6, 'recency': 0.4, 'popularity': 0.7},
            {'bm25': 0.4, 'recency': 0.3, 'popularity': 0.5},
        ]
        relevant_positions = [0, 1]

        updater.update_from_impression(ranking_scores, relevant_positions)

        assert updater.update_count == 1

    def test_weight_normalization(self):
        """Test weight normalization after updates."""
        weights = {'bm25': 0.4, 'recency': 0.3, 'popularity': 0.3}
        updater = OnlineLTRUpdater(weights)

        for _ in range(10):
            ranking_scores = {
                'bm25': np.random.random(),
                'recency': np.random.random(),
                'popularity': np.random.random()
            }
            updater.update_from_click("query", 1, ranking_scores)

        final_weights = updater.get_weights()
        # Weights should still be reasonable
        assert all(w >= -1 for w in final_weights.values())

    def test_update_stats(self):
        """Test statistics retrieval."""
        weights = {'bm25': 0.4, 'recency': 0.3, 'popularity': 0.3}
        updater = OnlineLTRUpdater(weights)

        ranking_scores = {'bm25': 0.8, 'recency': 0.5, 'popularity': 0.9}
        updater.update_from_click("test query", 1, ranking_scores)

        stats = updater.get_update_stats()
        assert stats['total_updates'] == 1
        assert 'current_weights' in stats
