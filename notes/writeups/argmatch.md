# Argument Checking

The argument checking logic in the model checker is currently quite wrong. It
needs to respect constant and wildcard arguments instead of ignoring them
incorrectly.

Named arguments need to be mapped onto actual LLVM values, which we can do with
the collectargs call. Then, we need a mapping from protobuf argument values to
these collected arguments. Once we have that, we can walk the assertion argument
list and check them against the actual function arguments.
