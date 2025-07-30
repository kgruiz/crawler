"""Tests for progress bar functionality."""

from unittest.mock import MagicMock, patch

import pytest
from rich.progress import Progress

from stealthcrawler.progress import make_progress


class TestMakeProgress:
    """Test make_progress function."""

    def test_make_progress_returns_progress_instance(self):
        """Test that make_progress returns a Progress instance."""
        progress = make_progress()

        assert isinstance(progress, Progress)

    def test_make_progress_has_correct_columns(self):
        """Test that make_progress creates Progress with expected columns."""
        progress = make_progress()

        # Check that it has columns (exact column types are implementation details,
        # but we can verify the structure)
        assert hasattr(progress, "columns")
        assert len(progress.columns) > 0

        # Verify it has spinner, text, percentage, bar, and time columns
        column_types = [type(col).__name__ for col in progress.columns]

        assert "SpinnerColumn" in column_types
        assert "TextColumn" in column_types
        assert "BarColumn" in column_types
        assert "MofNCompleteColumn" in column_types
        assert "TimeElapsedColumn" in column_types
        assert "TimeRemainingColumn" in column_types

    def test_make_progress_expand_enabled(self):
        """Test that progress bar is configured with expand=True."""
        progress = make_progress()

        # Progress should be configured to expand
        assert progress.expand is True

    def test_make_progress_can_add_task(self):
        """Test that tasks can be added to the progress bar."""
        progress = make_progress()

        task_id = progress.add_task("Test task", total=100)

        # Should return a valid task ID
        assert task_id is not None
        assert isinstance(
            task_id, (int, str)
        )  # Task ID can be int or string depending on implementation

    def test_make_progress_can_update_task(self):
        """Test that tasks can be updated in the progress bar."""
        progress = make_progress()

        task_id = progress.add_task("Test task", total=100)

        # Should be able to update task without error
        progress.update(task_id, advance=10)
        progress.update(task_id, description="Updated task")
        progress.update(task_id, total=200)

    def test_make_progress_context_manager(self):
        """Test that progress can be used as a context manager."""
        with make_progress() as progress:
            assert isinstance(progress, Progress)

            task_id = progress.add_task("Context task", total=50)
            progress.update(task_id, advance=25)

            # Should work within context manager

    def test_make_progress_multiple_tasks(self):
        """Test that multiple tasks can be managed simultaneously."""
        progress = make_progress()

        task1 = progress.add_task("Task 1", total=100)
        task2 = progress.add_task("Task 2", total=200)
        task3 = progress.add_task("Task 3", total=50)

        # All tasks should have different IDs
        assert task1 != task2
        assert task2 != task3
        assert task1 != task3

        # Should be able to update all tasks independently
        progress.update(task1, advance=10)
        progress.update(task2, advance=50)
        progress.update(task3, advance=25)

    def test_make_progress_column_configuration(self):
        """Test specific column configurations."""
        progress = make_progress()

        # Find text columns to check their configuration
        text_columns = [
            col for col in progress.columns if type(col).__name__ == "TextColumn"
        ]

        # Should have multiple text columns
        assert len(text_columns) > 0

        # At least one should be configured for task description
        # (We can't easily test the exact configuration without accessing private attributes)

    def test_make_progress_bar_column_configuration(self):
        """Test bar column configuration."""
        progress = make_progress()

        # Find bar column
        bar_columns = [
            col for col in progress.columns if type(col).__name__ == "BarColumn"
        ]

        # Should have exactly one bar column
        assert len(bar_columns) == 1

        bar_column = bar_columns[0]
        # Bar should be configured with flexible width (bar_width=None)
        assert bar_column.bar_width is None

    def test_make_progress_spinner_column(self):
        """Test spinner column presence."""
        progress = make_progress()

        # Find spinner column
        spinner_columns = [
            col for col in progress.columns if type(col).__name__ == "SpinnerColumn"
        ]

        # Should have exactly one spinner column
        assert len(spinner_columns) == 1

    def test_make_progress_percentage_display(self):
        """Test that percentage is properly displayed."""
        progress = make_progress()

        task_id = progress.add_task("Test task", total=100)
        progress.update(task_id, completed=50)

        # Progress should calculate percentage correctly
        # (We can't easily test the display without running the actual progress bar)
        task = progress.tasks[task_id]
        assert task.completed == 50
        assert task.total == 100

    def test_make_progress_time_columns(self):
        """Test presence of time-related columns."""
        progress = make_progress()

        column_types = [type(col).__name__ for col in progress.columns]

        # Should have both elapsed and remaining time columns
        assert "TimeElapsedColumn" in column_types
        assert "TimeRemainingColumn" in column_types

    def test_make_progress_mofn_column(self):
        """Test presence of M-of-N completion column."""
        progress = make_progress()

        column_types = [type(col).__name__ for col in progress.columns]

        # Should have M-of-N completion column
        assert "MofNCompleteColumn" in column_types


class TestProgressIntegration:
    """Integration tests for progress functionality."""

    def test_progress_with_realistic_workflow(self):
        """Test progress bar with a realistic crawling workflow."""
        with make_progress() as progress:
            # Simulate a crawling session
            task_id = progress.add_task("Discovering URLs...", total=1)

            # Simulate discovering more URLs
            progress.update(
                task_id, description="Scraping https://example.com", total=5
            )
            progress.update(task_id, advance=1)

            # Continue processing
            progress.update(
                task_id, description="Scraping https://example.com/page1", advance=1
            )
            progress.update(
                task_id, description="Scraping https://example.com/page2", advance=1
            )

            # Update total as more URLs are discovered
            progress.update(task_id, total=10)
            progress.update(
                task_id, description="Scraping https://example.com/page3", advance=1
            )

            # Verify final state
            task = progress.tasks[task_id]
            assert task.completed == 4
            assert task.total == 10

    def test_progress_task_completion(self):
        """Test completing a progress task."""
        with make_progress() as progress:
            task_id = progress.add_task("Test completion", total=100)

            # Complete the task
            progress.update(task_id, completed=100)

            task = progress.tasks[task_id]
            assert task.completed == 100
            assert task.total == 100
            assert task.finished  # Task should be marked as finished

    def test_progress_dynamic_total_adjustment(self):
        """Test adjusting total dynamically as work is discovered."""
        with make_progress() as progress:
            task_id = progress.add_task("Dynamic task", total=1)

            # Start with small total
            assert progress.tasks[task_id].total == 1

            # Expand total as more work is discovered
            progress.update(task_id, total=5)
            assert progress.tasks[task_id].total == 5

            # Continue expanding
            progress.update(task_id, total=20, advance=1)
            assert progress.tasks[task_id].total == 20
            assert progress.tasks[task_id].completed == 1

    @patch("rich.progress.Progress.console")
    def test_progress_console_integration(self, mock_console):
        """Test that progress integrates with console output."""
        # This test verifies that the progress bar can be created and used
        # without breaking when console operations are mocked

        with make_progress() as progress:
            task_id = progress.add_task("Console test", total=10)
            progress.update(task_id, advance=1)
            progress.update(task_id, description="Updated description")

            # Should complete without errors even with mocked console

    def test_progress_zero_total_handling(self):
        """Test handling of tasks with zero total."""
        with make_progress() as progress:
            task_id = progress.add_task("Zero total task", total=0)

            task = progress.tasks[task_id]
            assert task.total == 0

            # Should handle zero total gracefully
            progress.update(task_id, advance=0)

    def test_progress_negative_values_handling(self):
        """Test handling of edge cases with negative values."""
        with make_progress() as progress:
            task_id = progress.add_task("Edge case task", total=10)

            # Should handle negative advance gracefully
            # (depending on implementation, this might be clamped or raise an error)
            try:
                progress.update(task_id, advance=-1)
                # If no exception, verify the task state is reasonable
                task = progress.tasks[task_id]
                assert task.completed >= 0
            except ValueError:
                # Some implementations might raise ValueError for negative advance
                pass

    def test_progress_string_vs_numeric_ids(self):
        """Test that progress works with different task ID types."""
        with make_progress() as progress:
            # Create multiple tasks to test ID handling
            task_ids = []
            for i in range(3):
                task_id = progress.add_task(f"Task {i}", total=10)
                task_ids.append(task_id)

            # All task IDs should be valid and unique
            assert len(set(task_ids)) == 3

            # Should be able to update all tasks
            for task_id in task_ids:
                progress.update(task_id, advance=1)
