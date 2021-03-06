from _setup_test import *
State = state.State
StateTree = state.StateTree
from tree_util_lite.core import tree


class TestState(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestState, self).__init__(*args, **kwargs)
        self.output_state_file = Path(
            TEST_OUTPUT_DATA_LOCAL_REPO_DIR,
            VCS_FOLDER,
            REPO['FOLDER'],
            STATE['FOLDER'],
            's0'
        )
        self.sample_state_file = Path(
            TEST_SAMPLE_DATA_REPO_DIR,
            VCS_FOLDER,
            REPO['FOLDER'],
            STATE['FOLDER'],
            's0'
        )

    def setUp(self):
        create_output_repo_dir()
        create_output_workspace_dir()

    def tearDown(self):
        cleanup_output_data()

    def test_init(self):
        s0 = State(self.sample_state_file)
        self.assertEqual(s0.state_file, self.sample_state_file)
        self.assertEqual(s0.state_id, self.sample_state_file.name)
        self.assertIs(s0.previous, None)
        self.assertIs(s0.next, None)
        self.assertGreater(len(s0.session_list), 0)
        self.assertGreater(len(s0.data), 0)
        self.assertTrue(check_type(s0.state_tree, [state.StateTree]))
        self.assertTrue(check_type(s0.timestamp, [str]))

    def test_properties(self):

        s0 = State(self.sample_state_file)

        self.assertIs(s0.state_id, s0._state_id)
        self.assertIs(s0.state_file, s0._state_file)
        self.assertIs(s0.state_tree, s0._state_tree)
        self.assertIs(s0.timestamp, s0._timestamp)
        self.assertIs(s0.session_list, s0._session_list)
        self.assertIs(s0.data, s0._data)
        self.assertIs(s0.previous, s0._previous)
        self.assertIs(s0.next, s0._next)

    def test_update_and_save(self):
        workspace_hash = hashing.hash_workspace(TEST_OUTPUT_DATA_WORKSPACE_DIR)
        s0 = State(self.output_state_file)

        # save() is called in update()
        s0.update(
            workspace_hash,
            ['review'],
            {'message': 'test_state'}
        )

        # Test update()
        for v in workspace_hash.values():
            relative_path = v[WORKSPACE_HASH['RELATIVE_PATH_KEY']]
            hash_value = v[WORKSPACE_HASH['HASH_KEY']]
            n = s0.state_tree.search(relative_path)
            self.assertGreater(len(n), 0)
            self.assertEqual(n[0].data, hash_value)

        self.assertTrue(check_type(s0.timestamp, [str]))
        self.assertGreater(len(s0.session_list), 0)
        self.assertGreater(len(s0.data.values()), 0)

        # Test save()
        valid_data = load_json(self.output_state_file, VcsLogger())
        self.assertEqual(
            valid_data[STATE['CONTENT']['TIMESTAMP_KEY']],
            s0.timestamp
        )
        self.assertEqual(
            valid_data[STATE['CONTENT']['SESSION_LIST_KEY']],
            s0.session_list
        )
        self.assertEqual(
            valid_data[STATE['CONTENT']['DATA_KEY']],
            s0.data
        )

        self.assertGreater(len(valid_data[STATE['CONTENT']['FILE_KEY']]), 0)
        for p in valid_data[STATE['CONTENT']['FILE_KEY']]:
            n = s0.state_tree.search(Path(p).parent.as_posix())
            self.assertGreater(len(n), 0)

    def test_set_next(self):
        s0 = State(Path(TEST_OUTPUT_DATA_LOCAL_REPO_DIR).joinpath('path/to/s0'))
        s1 = State(Path(TEST_OUTPUT_DATA_LOCAL_REPO_DIR).joinpath('path/to/s1'))
        s0.set_next(s1)
        self.assertIs(s0.next, s1)
        self.assertIs(s1.previous, s0)

    def test_set_previous(self):
        s0 = State(Path(TEST_OUTPUT_DATA_LOCAL_REPO_DIR).joinpath('path/to/s0'))
        s1 = State(Path(TEST_OUTPUT_DATA_LOCAL_REPO_DIR).joinpath('path/to/s1'))
        s1.set_previous(s0)
        self.assertIs(s0.next, s1)
        self.assertIs(s1.previous, s0)

    def test_load(self):

        # load() is called in __init__()
        s0 = State(self.sample_state_file)

        valid_data = load_json(self.sample_state_file, VcsLogger())
        self.assertEqual(
            valid_data[STATE['CONTENT']['TIMESTAMP_KEY']],
            s0.timestamp
        )
        self.assertEqual(
            valid_data[STATE['CONTENT']['SESSION_LIST_KEY']],
            s0.session_list
        )
        self.assertEqual(
            valid_data[STATE['CONTENT']['DATA_KEY']],
            s0.data
        )

        self.assertGreater(len(valid_data[STATE['CONTENT']['FILE_KEY']]), 0)
        for p in valid_data[STATE['CONTENT']['FILE_KEY']]:
            n = s0.state_tree.search(Path(p).parent.as_posix())
            self.assertGreater(len(n), 0)

    def test_to_workspace_hash(self):

        s0 = State(self.sample_state_file)
        valid_data = load_json(self.sample_state_file, VcsLogger())
        real_workspace_hash = s0.to_workspace_hash()
        for k in valid_data[STATE['CONTENT']['FILE_KEY']]:
            p, d = tree.separate_path_data(k)
            self.assertIn(p, real_workspace_hash)
            self.assertEqual(d, real_workspace_hash[p][WORKSPACE_HASH['HASH_KEY']])


class TestStateTree(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestStateTree, self).__init__(*args, **kwargs)

    def setUp(self):
        create_output_repo_dir()

    def tearDown(self):
        cleanup_output_data()

    def test_init(self):
        workspace_hash = hashing.hash_workspace(TEST_OUTPUT_DATA_WORKSPACE_DIR)
        state_tree = StateTree(workspace_hash)
        for v in workspace_hash.values():
            relative_path = v[WORKSPACE_HASH['RELATIVE_PATH_KEY']]
            hash_value = v[WORKSPACE_HASH['HASH_KEY']]
            n = state_tree.search(relative_path)
            self.assertGreater(len(n), 0)
            self.assertEqual(n[0].data, hash_value)


@log_test(__file__)
def run():
    set_global_log_level(5)
    testcase_classes = [
        TestState,
        TestStateTree
    ]
    for tc in testcase_classes:
        testcase = unittest.TestLoader().loadTestsFromTestCase(tc)
        unittest.TextTestRunner(verbosity=2).run(testcase)


if __name__ == '__main__':
    run()
