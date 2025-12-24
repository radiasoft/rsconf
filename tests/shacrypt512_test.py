# Downloaded from https://eighty-twenty.org/2024/01/13/python-crypt-shacrypt
#
# SHAcrypt using SHA-512, after https://akkadia.org/drepper/SHA-crypt.txt.
#
# Copyright © 2024 Tony Garnock-Jones.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def test_all():
    from rsconf.shacrypt512 import shacrypt, password_ok

    _test_password = "Hello world!".encode("ascii")
    _test_salt = "saltstring".encode("ascii")
    _test_rounds = 5000
    _test_crypted_password = "$6$saltstring$svn8UoSVapNtMuq1ukKS4tPQd8iKwSMHWjl/O817G3uBnIFNjnQJuesI68u4OTLiBFdcbYEdFCoEOfaS35inz1"
    assert shacrypt(_test_password, _test_salt, _test_rounds) == _test_crypted_password
    assert password_ok(_test_password, _test_crypted_password)

    _test_password = "Hello world!".encode("ascii")
    _test_salt = "saltstringsaltstring".encode("ascii")
    _test_rounds = 10000
    _test_crypted_password = "$6$rounds=10000$saltstringsaltst$OW1/O6BYHV6BcXZu8QVeXbDWra3Oeqh0sbHbbMCVNSnCM/UrjmM0Dp8vOuZeHBy/YTBmSK6H9qs/y3RnOaw5v."
    assert shacrypt(_test_password, _test_salt, _test_rounds) == _test_crypted_password
    assert password_ok(_test_password, _test_crypted_password)
