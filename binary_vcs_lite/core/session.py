from binary_vcs_lite.common.util import *
from .state_chain import StateChain


class RevisionNotFound(VcsLiteError):
    """Revision not found."""


class Session(object):
    """Handle session data and behavior.

    Attributes:
        _session_id (str):
        _session_file (Path):
        _revision_data (dict):
        _detail_version_data (dict):

    Properties:
        session_id (str):
        session_file (Path):
        revision_data (dict):
        all_revision (list of int):
        latest_revision (int):

    Methods:
        sync_from_state_chain(state_chain)
        save()
        load()
        detail_file_version(revision, relative_path=None)

    """

    def __init__(self, session_file):
        """
        Args:
            session_file (str|Path): A session file
        """
        super(Session, self).__init__()
        check_type(session_file, [str, Path])

        session_file = Path(session_file)

        self._session_file = session_file
        self._session_id = session_file.name
        self._revision_data = {}
        self._detail_version_data = {}
        if session_file.exists():
            self.load()

    @property
    def session_id(self):
        """str: """
        return self._session_id

    @property
    def session_file(self):
        """Path: """
        return self._session_file

    @property
    def revision_data(self):
        """dict: """
        return self._revision_data

    @property
    def all_revision(self):
        """list of int: """
        return sorted([int(r) for r in self._revision_data])

    @property
    def latest_revision(self):
        """int: """
        all_rev = self.all_revision
        return all_rev[-1] if all_rev else 0

    def sync_from_state_chain(self, state_chain):
        """
        Args:
            state_chain (StateChain):
        """
        check_type(state_chain, [StateChain])

        # Iterate through `state_chain` to update `self._revision_data`
        state_list = []
        for state_id in state_chain.all_state_id:
            state = state_chain.state_data[state_id]
            if self.session_id in state.session_list:
                state_list.append(state)

        for i, state in enumerate(state_list):
            rev = i + 1
            if rev not in self._revision_data:
                self._revision_data[rev] = state.state_id

        # Update `self._detail_version_data`
        for rev in self.all_revision:
            rev = str(rev)
            if rev not in self._detail_version_data:
                pre_rev = str(int(rev) - 1)
                s2_id = self._revision_data[rev]
                if rev == 1:
                    s1_id = s2_id
                else:
                    s1_id = self._revision_data[pre_rev]
                s1 = state_chain.state_data[s1_id]
                s2 = state_chain.state_data[s2_id]
                state_diff = state_chain.compare_state(s1, s2)

                # Detail file version of previous revision
                if pre_rev in self._detail_version_data:
                    pre_detail_ver = self._detail_version_data[pre_rev]
                else:
                    pre_detail_ver = {}

                # Detail file version of current revision
                cur_detail_ver = {}

                for k in state_diff['unchanged']:
                    if k in pre_detail_ver:
                        cur_detail_ver[k] = pre_detail_ver[k]
                    else:
                        cur_detail_ver[k] = 1

                for k in state_diff['modified']:
                    if k in pre_detail_ver:
                        cur_detail_ver[k] = pre_detail_ver[k] + 1

                for k in state_diff['added']:
                    tmp_rev = pre_rev
                    found = 0
                    while not found:
                        if tmp_rev == '0':
                            break
                        if tmp_rev in self._detail_version_data:
                            if k in self._detail_version_data[tmp_rev]:
                                # Continue from some version in history
                                cur_detail_ver[k] = self._detail_version_data[tmp_rev] + 1
                                found = 1
                        tmp_rev -= str(1)

                    # Added for the first time
                    if not found:
                        cur_detail_ver[k] = 1

                self._detail_version_data[rev] = cur_detail_ver

        self.save()

    def save(self):
        """Save session attributes to session file.

        Returns:
            bool:
        """
        rev_key = SESSION['CONTENT']['REVISION_KEY']
        ver_key = SESSION['CONTENT']['DETAIL_VERSION_KEY']
        data[rev_key] = self._revision_data
        data[ver_key] = self._detail_version_data
        save_json(data, self._session_file)
        return 1

    def load(self):
        """Load session attributes from session file.

        Returns:
            bool:
        """
        rev_key = SESSION['CONTENT']['REVISION_KEY']
        ver_key = SESSION['CONTENT']['DETAIL_VERSION_KEY']
        data = load_json(self._session_file)
        if rev_key not in data or ver_key not in data:
            return 0
        self._revision_data = data[rev_key]
        self._detail_version_data = data[ver_key]
        return 1

    def detail_file_version(self, revision=None, relative_path=None):
        """
        Args:
            revision (int, None by default):
            relative_path (str|Path, None by default):
        Raises:
            RevisionNotFound:
        Returns:
            dict:
        """
        check_type(revision, [int, type(None)])
        check_type(relative_path, [str, Path, type(None)])

        revision = revision if revision else self.latest_revision
        if revision not in self._detail_version_data:
            raise RevisionNotFound()
        file_versions = self._detail_version_data[revision]
        if relative_path:
            relative_path = str(relative_path)
            for k in list(file_versions):
                if relative_path != k:
                    file_versions.pop(k)
        return file_versions
