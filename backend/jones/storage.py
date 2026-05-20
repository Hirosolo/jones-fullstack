"""
Custom storage backends.

`SequentialFileSystemStorage` overrides Django 5's default collision suffix
(7 random chars like `_VmmY2L0`) with a predictable `-N` counter, so a
second upload of `foo.jpg` becomes `foo-1.jpg`, then `foo-2.jpg`, etc.

Why: predictable filenames let the FE emit canonical image URLs like
`https://api.jones.com/media/<slug>-<N>.<ext>` without a hardcoded
override map. Random suffixes break that contract.
"""
import os

from django.core.files.storage import FileSystemStorage


class SequentialFileSystemStorage(FileSystemStorage):
    """FileSystemStorage that resolves name collisions with -1, -2, -3 …

    On Django 5 the base `get_available_name()` appends a 7-char random
    string when a file already exists at the target path (a security
    hardening change in 4.2+). For product images we need predictable
    filenames so the SEO layer can build canonical URLs from the slug
    alone — so we override the collision strategy.

    Behavior:
        upload `foo.jpg` → exists → store as `foo-1.jpg`
        upload `foo.jpg` again   → store as `foo-2.jpg`
        ...

    The `name` already passed in by Django is the prospective path
    (after upload_to() / clean()), so we only need to walk a counter
    until the file does not exist.
    """

    # Hard cap to avoid an infinite loop on a pathological filesystem.
    _MAX_SUFFIX = 10_000

    def get_available_name(self, name, max_length=None):
        if not self.exists(name) and (max_length is None or len(name) <= max_length):
            return name

        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)

        # If the incoming name itself already ends with -<digits>, treat
        # the digits as the starting counter so a re-upload of foo-2.jpg
        # becomes foo-2-1.jpg (not foo-2.jpg → foo-3.jpg, which would
        # collide with a possibly unrelated foo-3.jpg).
        counter = 1
        while counter <= self._MAX_SUFFIX:
            candidate_name = f'{file_root}-{counter}{file_ext}'
            candidate = os.path.join(dir_name, candidate_name) if dir_name else candidate_name

            if max_length is not None and len(candidate) > max_length:
                # Trim the root to fit, keep the suffix + extension intact.
                trim = len(candidate) - max_length
                trimmed_root = file_root[:-trim].rstrip('-_') if trim < len(file_root) else file_root
                candidate_name = f'{trimmed_root}-{counter}{file_ext}'
                candidate = os.path.join(dir_name, candidate_name) if dir_name else candidate_name

            if not self.exists(candidate):
                return candidate
            counter += 1

        raise RuntimeError(
            f'SequentialFileSystemStorage: exhausted {self._MAX_SUFFIX} '
            f'suffix slots for {name!r}'
        )
