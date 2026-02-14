"""Tests for MCP server functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from nvim_markdown_notes_memgraph import entities
from nvim_markdown_notes_memgraph.server import MemgraphNotesServer


class TestEntityExtraction:
    """Test entity extraction functions."""

    def test_extract_wikilinks_single(self):
        """Test extracting a single wikilink."""
        line = "This is a [[note]] reference."
        result = entities.extract_wikilinks(line, 1, "/notes")

        assert len(result) == 1
        assert result[0]['target'] == 'note'
        assert result[0]['target_path'] == '/notes/note.md'
        assert result[0]['line_number'] == 1

    def test_extract_wikilinks_multiple(self):
        """Test extracting multiple wikilinks from one line."""
        line = "See [[first]] and [[second]] for details."
        result = entities.extract_wikilinks(line, 2, "/notes")

        assert len(result) == 2
        assert result[0]['target'] == 'first'
        assert result[1]['target'] == 'second'
        assert result[0]['line_number'] == 2
        assert result[1]['line_number'] == 2

    def test_extract_wikilinks_with_alias(self):
        """Test extracting wikilink with alias [[target|alias]]."""
        line = "See [[actual-note|display name]]."
        result = entities.extract_wikilinks(line, 1, "/notes")

        assert len(result) == 1
        assert result[0]['target'] == 'actual-note'
        assert result[0]['target_path'] == '/notes/actual-note.md'

    def test_extract_wikilinks_none(self):
        """Test line with no wikilinks."""
        line = "This is just plain text."
        result = entities.extract_wikilinks(line, 1, "/notes")

        assert len(result) == 0

    def test_extract_mentions_single(self):
        """Test extracting a single @mention."""
        line = "Meet with @alice tomorrow."
        result = entities.extract_mentions(line, 1)

        assert len(result) == 1
        assert result[0]['name'] == 'alice'
        assert result[0]['line_number'] == 1

    def test_extract_mentions_multiple(self):
        """Test extracting multiple mentions."""
        line = "Meeting with @alice and @bob-smith."
        result = entities.extract_mentions(line, 3)

        assert len(result) == 2
        assert result[0]['name'] == 'alice'
        assert result[1]['name'] == 'bob-smith'
        assert result[0]['line_number'] == 3
        assert result[1]['line_number'] == 3

    def test_extract_mentions_skip_email(self):
        """Test that email addresses are not extracted as mentions."""
        line = "Contact alice@example.com for details."
        result = entities.extract_mentions(line, 1)

        # Should filter out email
        assert len(result) == 0

    def test_extract_mentions_skip_email_variations(self):
        """Test filtering various email TLDs."""
        line = "Emails: @example.com, @test.org, @demo.io, @sample.co"
        result = entities.extract_mentions(line, 1)

        # All should be filtered as emails
        assert len(result) == 0

    def test_extract_mentions_hyphen_underscore(self):
        """Test mentions with hyphens and underscores."""
        line = "Mention @john-doe and @jane_smith."
        result = entities.extract_mentions(line, 1)

        assert len(result) == 2
        assert result[0]['name'] == 'john-doe'
        assert result[1]['name'] == 'jane_smith'

    def test_extract_hashtags_single(self):
        """Test extracting a single hashtag."""
        line = "This is about #project."
        result = entities.extract_hashtags(line, 1)

        assert len(result) == 1
        assert result[0]['name'] == 'project'
        assert result[0]['line_number'] == 1

    def test_extract_hashtags_multiple(self):
        """Test extracting multiple hashtags."""
        line = "Topics: #tech #ops #meeting"
        result = entities.extract_hashtags(line, 2)

        assert len(result) == 3
        assert result[0]['name'] == 'tech'
        assert result[1]['name'] == 'ops'
        assert result[2]['name'] == 'meeting'

    def test_extract_hashtags_exclude_false_positives(self):
        """Test that excluded hashtags are filtered out."""
        line = "See #gid #browse #edit #resource for links."
        result = entities.extract_hashtags(line, 1)

        # All are in EXCLUDED_HASHTAGS
        assert len(result) == 0

    def test_extract_hashtags_skip_url_fragments(self):
        """Test that URL fragments after / are filtered by negative lookbehind."""
        line = "Visit https://example.com/#section for details."
        result = entities.extract_hashtags(line, 1)

        # The negative lookbehind (?<![/=]) filters out #section after /
        assert len(result) == 0

    def test_extract_hashtags_skip_hex_color_with_equals(self):
        """Test that hex colors after = are filtered by negative lookbehind."""
        line = "Color is background=#000000"
        result = entities.extract_hashtags(line, 1)

        # The negative lookbehind (?<![/=]) filters out #000000 after =
        assert len(result) == 0

    def test_extract_hashtags_mixed_valid_invalid(self):
        """Test line with both valid hashtags and excluded ones."""
        line = "Tags: #project #gid #meeting #browse"
        result = entities.extract_hashtags(line, 1)

        # Only project and meeting should be extracted
        assert len(result) == 2
        names = [tag['name'] for tag in result]
        assert 'project' in names
        assert 'meeting' in names
        assert 'gid' not in names
        assert 'browse' not in names

    def test_extract_from_file_complete(self):
        """Test extracting all entities from a markdown file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Meeting Notes\n")
            f.write("Met with @alice about [[project-alpha]].\n")
            f.write("Topics: #tech #ops\n")
            f.write("Follow up with @bob-smith.\n")
            temp_path = f.name

        try:
            notes_root = os.path.dirname(temp_path)
            result = entities.extract_from_file(temp_path, notes_root)

            assert result['path'] == temp_path
            assert result['title'] == 'Meeting Notes'
            assert '# Meeting Notes' in result['content']

            # Check wikilinks
            assert len(result['wikilinks']) == 1
            assert result['wikilinks'][0]['target'] == 'project-alpha'
            assert result['wikilinks'][0]['line_number'] == 2

            # Check mentions
            assert len(result['mentions']) == 2
            mention_names = [m['name'] for m in result['mentions']]
            assert 'alice' in mention_names
            assert 'bob-smith' in mention_names

            # Check hashtags
            assert len(result['hashtags']) == 2
            hashtag_names = [h['name'] for h in result['hashtags']]
            assert 'tech' in hashtag_names
            assert 'ops' in hashtag_names
        finally:
            os.unlink(temp_path)

    def test_extract_from_file_empty(self):
        """Test extracting from empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            result = entities.extract_from_file(temp_path)

            assert result['path'] == temp_path
            assert result['content'] == ''
            assert result['wikilinks'] == []
            assert result['mentions'] == []
            assert result['hashtags'] == []
        finally:
            os.unlink(temp_path)

    def test_extract_from_file_title_from_heading(self):
        """Test that title is extracted from first heading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# My Title\n")
            f.write("Some content.\n")
            temp_path = f.name

        try:
            result = entities.extract_from_file(temp_path)

            # Should strip the '# ' prefix
            assert result['title'] == 'My Title'
        finally:
            os.unlink(temp_path)

    def test_extract_from_file_title_from_first_line(self):
        """Test that title is extracted from first line if no heading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Just some content without a heading.\n")
            temp_path = f.name

        try:
            result = entities.extract_from_file(temp_path)

            # Should use first line as title
            assert result['title'] == 'Just some content without a heading.'
        finally:
            os.unlink(temp_path)

    def test_extract_from_file_nonexistent(self):
        """Test extracting from nonexistent file."""
        result = entities.extract_from_file('/nonexistent/file.md')

        assert result['path'] == '/nonexistent/file.md'
        assert result['content'] == ''
        assert result['wikilinks'] == []
        assert result['mentions'] == []
        assert result['hashtags'] == []


class TestMemgraphNotesServer:
    """Test MemgraphNotesServer class methods."""

    def test_init_default_values(self):
        """Test server initialization with default values."""
        server = MemgraphNotesServer()

        assert server.host == "localhost"
        assert server.port == 7687
        assert server.notes_root == os.getcwd()
        assert server.connection is None

    def test_init_custom_values(self):
        """Test server initialization with custom values."""
        server = MemgraphNotesServer(
            host="custom-host",
            port=9999,
            notes_root="/custom/notes"
        )

        assert server.host == "custom-host"
        assert server.port == 9999
        assert server.notes_root == "/custom/notes"

    def test_read_note_content_existing_file(self):
        """Test reading content from existing note."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Note\nSome content.")
            temp_path = f.name

        try:
            notes_root = os.path.dirname(temp_path)
            server = MemgraphNotesServer(notes_root=notes_root)

            content = server.read_note_content(temp_path)

            assert "# Test Note" in content
            assert "Some content." in content
        finally:
            os.unlink(temp_path)

    def test_read_note_content_nonexistent_file(self):
        """Test reading content from nonexistent file."""
        server = MemgraphNotesServer()

        content = server.read_note_content('/nonexistent/file.md')

        assert "Note not found" in content

    def test_read_note_content_relative_path(self):
        """Test reading content with relative path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a note in temporary directory
            note_path = os.path.join(tmpdir, 'test.md')
            with open(note_path, 'w') as f:
                f.write("Test content")

            server = MemgraphNotesServer(notes_root=tmpdir)

            # Read with relative path
            content = server.read_note_content('test.md')

            assert "Test content" in content

    def test_extract_from_file_delegates_to_entities(self):
        """Test that extract_from_file delegates to entities module."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test\n[[link]] @mention #tag")
            temp_path = f.name

        try:
            notes_root = os.path.dirname(temp_path)
            server = MemgraphNotesServer(notes_root=notes_root)

            result = server.extract_from_file(temp_path)

            # Should return same structure as entities.extract_from_file
            assert 'path' in result
            assert 'title' in result
            assert 'wikilinks' in result
            assert 'mentions' in result
            assert 'hashtags' in result

            assert len(result['wikilinks']) == 1
            assert len(result['mentions']) == 1
            assert len(result['hashtags']) == 1
        finally:
            os.unlink(temp_path)


class TestMemgraphServerQueryBuilding:
    """Test query building for Memgraph operations (mocked)."""

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_get_backlinks_query_structure(self, mock_mgclient):
        """Test that get_backlinks builds correct query."""
        # Create mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ['/notes/source1.md', 'Source One', 10],
            ['/notes/source2.md', 'Source Two', 20]
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        server.connect()

        results = server.get_backlinks('/notes/target.md')

        # Verify cursor.execute was called
        assert mock_cursor.execute.called

        # Verify the query contains expected patterns
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert 'MATCH' in query
        assert 'LINKS_TO' in query
        assert params['path'] == '/notes/target.md'

        # Verify results structure
        assert len(results) == 2
        assert results[0]['path'] == '/notes/source1.md'
        assert results[0]['title'] == 'Source One'
        assert results[0]['line'] == 10

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_find_by_tag_strips_hash_prefix(self, mock_mgclient):
        """Test that find_by_tag strips # prefix."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        server.connect()

        # Call with # prefix
        server.find_by_tag('#project')

        # Verify query was called with stripped tag
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]
        assert params['tag'] == 'project'

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_find_by_mention_strips_at_prefix(self, mock_mgclient):
        """Test that find_by_mention strips @ prefix."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        server.connect()

        # Call with @ prefix
        server.find_by_mention('@alice')

        # Verify query was called with stripped name
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]
        assert params['person'] == 'alice'

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_get_related_returns_structured_data(self, mock_mgclient):
        """Test that get_related returns properly structured data."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ['/notes/related.md', 'Related Note', 3, ['Tag: project', 'Person: alice']]
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        server.connect()

        results = server.get_related('/notes/source.md')

        assert len(results) == 1
        assert results[0]['path'] == '/notes/related.md'
        assert results[0]['title'] == 'Related Note'
        assert results[0]['shared_count'] == 3
        assert results[0]['connections'] == ['Tag: project', 'Person: alice']

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_get_note_context_complete_structure(self, mock_mgclient):
        """Test that get_note_context returns complete structure."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            [
                'My Note',                                      # title
                '/notes/my-note.md',                            # path
                [{'path': '/notes/link1.md', 'title': 'Link 1'}],  # outgoing_links
                ['tag1', 'tag2'],                              # tags
                ['alice', 'bob'],                               # mentions
                [{'path': '/notes/back1.md', 'title': 'Back 1'}]   # backlinks
            ]
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        server.connect()

        result = server.get_note_context('/notes/my-note.md')

        assert result['title'] == 'My Note'
        assert result['path'] == '/notes/my-note.md'
        assert len(result['outgoing_links']) == 1
        assert len(result['tags']) == 2
        assert len(result['mentions']) == 2
        assert len(result['backlinks']) == 1

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_get_graph_stats_returns_dict(self, mock_mgclient):
        """Test that get_graph_stats returns statistics dict."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Each query() calls is_connected() first, then the actual query
        # So we need to mock fetchall to return values for both
        # Use a simple counter that returns different values
        call_count = [0]
        def mock_fetchall():
            call_count[0] += 1
            # Odd calls are is_connected checks, even calls are actual queries
            if call_count[0] % 2 == 1:
                return [[1]]  # is_connected check
            else:
                # Return different counts for each stat query
                return [[call_count[0] * 10]]

        mock_cursor.fetchall.side_effect = mock_fetchall
        mock_conn.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        server.connect()

        stats = server.get_graph_stats()

        # Verify structure and that we got numeric values
        assert isinstance(stats, dict)
        assert 'notes' in stats
        assert 'tags' in stats
        assert 'persons' in stats
        assert 'links' in stats
        assert 'mentions' in stats
        assert 'tag_usages' in stats

        # All values should be numeric (from our mock)
        for key, value in stats.items():
            assert isinstance(value, int)

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_search_notes_by_title(self, mock_mgclient):
        """Test searching notes by title pattern."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ['/notes/project-alpha.md', 'Project Alpha'],
            ['/notes/project-beta.md', 'Project Beta']
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        server.connect()

        results = server.search_notes('project')

        # Verify query was called with correct parameters
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]
        assert params['query'] == 'project'

        # Verify results
        assert len(results) == 2
        assert results[0]['title'] == 'Project Alpha'

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_get_all_tags_with_counts(self, mock_mgclient):
        """Test getting all tags with usage counts."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ['project', 10],
            ['tech', 5],
            ['meeting', 3]
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        server.connect()

        results = server.get_all_tags()

        assert len(results) == 3
        assert results[0]['name'] == 'project'
        assert results[0]['count'] == 10
        assert results[1]['name'] == 'tech'
        assert results[1]['count'] == 5

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_get_all_persons_with_counts(self, mock_mgclient):
        """Test getting all persons with mention counts."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ['alice', 15],
            ['bob', 8]
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        server.connect()

        results = server.get_all_persons()

        assert len(results) == 2
        assert results[0]['name'] == 'alice'
        assert results[0]['mention_count'] == 15

    def test_search_note_content_in_files(self):
        """Test full-text search in note content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test notes
            note1_path = os.path.join(tmpdir, 'note1.md')
            with open(note1_path, 'w') as f:
                f.write("# Note One\nThis contains searchterm in content.\n")

            note2_path = os.path.join(tmpdir, 'note2.md')
            with open(note2_path, 'w') as f:
                f.write("# Note Two\nNo match here.\n")

            note3_path = os.path.join(tmpdir, 'note3.md')
            with open(note3_path, 'w') as f:
                f.write("# Note Three\nAlso has SEARCHTERM (case insensitive).\n")

            server = MemgraphNotesServer(notes_root=tmpdir)

            results = server.search_note_content('searchterm')

            # Should find note1 and note3
            assert len(results) == 2
            paths = [r['path'] for r in results]
            assert note1_path in paths
            assert note3_path in paths
            assert note2_path not in paths

    def test_find_journals_by_date_range_query(self):
        """Test journal date range query building."""
        with patch('nvim_markdown_notes_memgraph.server.mgclient') as mock_mgclient:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                ['/notes/journal/2024-01-15.md', '2024-01-15', '2024-01-15.md']
            ]
            mock_conn.cursor.return_value = mock_cursor
            mock_mgclient.connect.return_value = mock_conn

            server = MemgraphNotesServer()
            server.connect()

            results = server.find_journals_by_date_range('2024-01-15', '2024-01-20')

            # Verify query parameters
            call_args = mock_cursor.execute.call_args
            params = call_args[0][1]
            assert params['start_date'] == '2024-01-15'
            assert params['end_date'] == '2024-01-20'

    def test_find_notes_by_filename_pattern_query(self):
        """Test filename pattern search query building."""
        with patch('nvim_markdown_notes_memgraph.server.mgclient') as mock_mgclient:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_mgclient.connect.return_value = mock_conn

            server = MemgraphNotesServer()
            server.connect()

            server.find_notes_by_filename_pattern('test')

            # Verify query was called with pattern
            call_args = mock_cursor.execute.call_args
            params = call_args[0][1]
            assert params['pattern'] == 'test'


class TestConnectionManagement:
    """Test connection management methods."""

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_connect_success(self, mock_mgclient):
        """Test successful connection to Memgraph."""
        mock_conn = MagicMock()
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        result = server.connect()

        assert result is True
        assert server.connection is not None
        mock_mgclient.connect.assert_called_once_with(host='localhost', port=7687)

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_connect_failure(self, mock_mgclient):
        """Test connection failure handling."""
        mock_mgclient.connect.side_effect = Exception("Connection failed")

        server = MemgraphNotesServer()
        result = server.connect()

        assert result is False
        assert server.connection is None

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_is_connected_when_connected(self, mock_mgclient):
        """Test is_connected returns True when connected."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [[1]]
        mock_conn.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        server.connect()

        assert server.is_connected() is True

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_is_connected_when_disconnected(self, mock_mgclient):
        """Test is_connected returns False when disconnected."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Connection lost")
        mock_conn.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        server.connect()

        # Connection test fails
        assert server.is_connected() is False
        # Connection should be cleared
        assert server.connection is None

    @patch('nvim_markdown_notes_memgraph.server.mgclient')
    def test_ensure_connected_reconnects(self, mock_mgclient):
        """Test ensure_connected reconnects if needed."""
        mock_conn = MagicMock()
        mock_mgclient.connect.return_value = mock_conn

        server = MemgraphNotesServer()
        # Initially not connected
        assert server.connection is None

        # ensure_connected should connect
        result = server.ensure_connected()

        assert result is True
        assert server.connection is not None
