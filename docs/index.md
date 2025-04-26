# Home

<style>
    .md-content .md-typeset h1 { display: none; }
</style>

---


## Get Started
Install the requirements

### 1. Install UV

=== "Linux or MacOS"
    <!-- termynal -->
    ```
    $ wget -qO- https://astral.sh/uv/install.sh | sh
    ---> 100%
    Installed
    ```

=== "Windows"
    <!-- termynal -->
    ```
    $ powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ---> 100%
    Installed
    ```

### 2. Install Libraries

=== "Linux or MacOS"
    <!-- termynal -->
    ```
    $ uv sync
    ---> 100%
    $ source .venv/bin/activate
    ```

=== "Windows"
    <!-- termynal -->
    ```
    $ uv sync
    ---> 100%
    $ .venv\Scripts\activate
    ```
