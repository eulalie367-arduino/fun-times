"""Build timelines of events and entity activities.

Constructs chronological sequences of events and entity interactions.
"""

from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TimelineEvent:
    """Represents an event in a timeline."""

    timestamp: float
    entity: str
    event_type: str
    description: str
    related_entities: List[str]
    importance: float = 0.5

    def __lt__(self, other):
        """Enable sorting by timestamp."""
        return self.timestamp < other.timestamp


class TimelineBuilder:
    """Build entity activity timelines."""

    def __init__(self):
        """Initialize timeline builder."""
        self.events: List[TimelineEvent] = []
        self.entity_timelines: Dict[str, List[TimelineEvent]] = {}

    def add_event(
        self,
        timestamp: float,
        entity: str,
        event_type: str,
        description: str,
        related_entities: Optional[List[str]] = None,
        importance: float = 0.5
    ):
        """Add event to timeline.

        Args:
            timestamp: Event timestamp (unix time)
            entity: Primary entity involved
            event_type: Type of event
            description: Event description
            related_entities: Other entities involved
            importance: Event importance (0-1)
        """
        event = TimelineEvent(
            timestamp=timestamp,
            entity=entity,
            event_type=event_type,
            description=description,
            related_entities=related_entities or [],
            importance=importance
        )

        self.events.append(event)

        if entity not in self.entity_timelines:
            self.entity_timelines[entity] = []

        self.entity_timelines[entity].append(event)

        logger.debug(f"Added event: {entity} - {event_type}")

    def get_entity_timeline(self, entity: str) -> List[TimelineEvent]:
        """Get chronological timeline for entity.

        Args:
            entity: Entity name

        Returns:
            Sorted list of events for entity
        """
        timeline = self.entity_timelines.get(entity, [])
        return sorted(timeline, key=lambda e: e.timestamp)

    def get_event_sequence(
        self,
        start_time: float,
        end_time: float
    ) -> List[TimelineEvent]:
        """Get events within time range.

        Args:
            start_time: Start timestamp
            end_time: End timestamp

        Returns:
            Sorted events in time range
        """
        filtered = [
            event for event in self.events
            if start_time <= event.timestamp <= end_time
        ]

        return sorted(filtered, key=lambda e: e.timestamp)

    def find_concurrent_events(self, window_seconds: float = 3600) -> List[List[TimelineEvent]]:
        """Find events that occur concurrently.

        Args:
            window_seconds: Time window for concurrency

        Returns:
            List of concurrent event groups
        """
        if not self.events:
            return []

        sorted_events = sorted(self.events, key=lambda e: e.timestamp)
        concurrent_groups = []
        current_group = [sorted_events[0]]

        for event in sorted_events[1:]:
            if event.timestamp - current_group[0].timestamp <= window_seconds:
                current_group.append(event)
            else:
                if len(current_group) > 1:
                    concurrent_groups.append(current_group)

                current_group = [event]

        if len(current_group) > 1:
            concurrent_groups.append(current_group)

        return concurrent_groups

    def get_important_events(
        self,
        entity: str,
        importance_threshold: float = 0.7
    ) -> List[TimelineEvent]:
        """Get important events for entity.

        Args:
            entity: Entity name
            importance_threshold: Minimum importance

        Returns:
            Important events sorted chronologically
        """
        timeline = self.get_entity_timeline(entity)

        important = [
            event for event in timeline
            if event.importance >= importance_threshold
        ]

        return important

    def get_event_summary(self, entity: str) -> Dict[str, int]:
        """Get summary of events for entity.

        Args:
            entity: Entity name

        Returns:
            Dictionary with event counts by type
        """
        timeline = self.get_entity_timeline(entity)
        summary = {}

        for event in timeline:
            summary[event.event_type] = summary.get(event.event_type, 0) + 1

        return summary

    def get_stats(self) -> Dict[str, int]:
        """Get timeline statistics.

        Returns:
            Dictionary with timeline metrics
        """
        return {
            'total_events': len(self.events),
            'entities': len(self.entity_timelines),
            'event_types': len(set(e.event_type for e in self.events))
        }
