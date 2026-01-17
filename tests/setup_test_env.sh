#!/bin/bash
set -euo pipefail

echo "=== Automated Firefly III v6 Test Setup ==="
echo ""

# --- Step 0: Detect Container Engine ---
if command -v docker >/dev/null 2>&1; then
    CONTAINER_ENGINE="docker"
elif command -v podman >/dev/null 2>&1; then
    CONTAINER_ENGINE="podman"
else
    echo "✗ Error: Neither docker nor podman found in PATH."
    exit 1
fi

# Determine if we use 'docker compose' or 'podman-compose'
# Most modern systems use the 'compose' plugin for both
if $CONTAINER_ENGINE compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="$CONTAINER_ENGINE compose"
else
    # Fallback for older podman/docker setups
    DOCKER_COMPOSE="${CONTAINER_ENGINE}-compose"
fi

echo "→ Using container engine: $CONTAINER_ENGINE ($DOCKER_COMPOSE)"

# Step 1: Reset and start Firefly III
echo "Step 1: Starting Firefly III (with clean database)..."
$DOCKER_COMPOSE -f docker-compose.test.yml down -v --remove-orphans > /dev/null 2>&1 || true
$DOCKER_COMPOSE -f docker-compose.test.yml up -d

# Step 2: Wait for Firefly to be healthy
echo "Step 2: Waiting for Firefly III to initialize..."
MAX_RETRIES=30
RETRY_COUNT=0
HEALTH_URL="http://localhost:8080/health"

until $(curl --output /dev/null --silent --head --fail "$HEALTH_URL"); do
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
      echo -e "\n✗ Firefly III failed to start."
      $DOCKER_COMPOSE -f docker-compose.test.yml logs firefly-app | tail -n 20
      exit 1
    fi
    echo -n "."
    RETRY_COUNT=$((RETRY_COUNT+1))
    sleep 2
done

echo -e "\n✓ Health check passed. Finalizing database migrations..."
$DOCKER_COMPOSE -f docker-compose.test.yml exec -T firefly-app php artisan migrate --force > /dev/null 2>&1

# Step 3: Create User, User Group, and Link via Foreign Key
echo ""
echo "Step 3: Provisioning user and administration group..."

$DOCKER_COMPOSE -f docker-compose.test.yml exec -T firefly-app php -r "
    require 'vendor/autoload.php';
    \$app = require_once 'bootstrap/app.php';
    \$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

    try {
        \Illuminate\Support\Facades\DB::beginTransaction();

        // Get or create default group (#1) - Firefly III uses this for API requests
        \$group = \FireflyIII\Models\UserGroup::findOrNew(1);
        if (!\$group->exists) {
            \$group->id = 1;
            \$group->title = 'Default User Group';
            \$group->save();
        }

        // Create or update user, link to group #1
        \$user = \FireflyIII\User::firstOrNew(['email' => 'test@lampyrid.local']);
        \$user->password = \Illuminate\Support\Facades\Hash::make('secret_password_123');
        \$user->user_group_id = 1; // Must use group #1 for API access
        \$user->email = 'test@lampyrid.local';
        \$user->save();

        // Create group membership entry - this is required for API authorization
        \$existing = \Illuminate\Support\Facades\DB::table('group_memberships')
            ->where('user_id', \$user->id)
            ->where('user_group_id', \$group->id)
            ->first();

        if (!\$existing) {
            \Illuminate\Support\Facades\DB::table('group_memberships')->insert([
                'user_id' => \$user->id,
                'user_group_id' => \$group->id,
                'user_role_id' => 21, // owner role ID
                'created_at' => date('Y-m-d H:i:s'),
                'updated_at' => date('Y-m-d H:i:s'),
            ]);
        }

        \Illuminate\Support\Facades\DB::commit();
        echo '✓ User test@lampyrid.local created and linked to default Group #1' . PHP_EOL;
    } catch (\Exception \$e) {
        \Illuminate\Support\Facades\DB::rollBack();
        fwrite(STDERR, '✗ Provisioning Error: ' . \$e->getMessage() . PHP_EOL);
        exit(1);
    }
"

# Step 4: Create personal access client
echo ""
echo "Step 4: Creating OAuth personal access client..."
$DOCKER_COMPOSE -f docker-compose.test.yml exec -T firefly-app \
    php artisan passport:client --personal --no-interaction --name="Test Client" > /dev/null 2>&1

# Step 5: Generate access token
echo ""
echo "Step 5: Generating API access token..."
TOKEN=$($DOCKER_COMPOSE -f docker-compose.test.yml exec -T firefly-app php -r "
    require 'vendor/autoload.php';
    \$app = require_once 'bootstrap/app.php';
    \$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
    
    \$user = \FireflyIII\User::where('email', 'test@lampyrid.local')->first();
    if (\$user) {
        echo \$user->createToken('CI Token')->accessToken;
    }
" | tail -n 1 | tr -d '\r')

if [ -z "$TOKEN" ]; then
    echo "✗ Failed to generate token."
    exit 1
fi
echo "✓ Token generated: ${TOKEN:0:40}..."

# Step 6: Save configuration
mkdir -p tests
cat > tests/.env.test << EOF
FIREFLY_BASE_URL=http://localhost:8080
FIREFLY_TOKEN=$TOKEN
LOGGING_LEVEL=DEBUG
EOF
echo "✓ Configuration saved to tests/.env.test"

# Step 7 & 8: Verify
echo ""
echo "Step 7: Test setup complete!"
echo ""
echo "Step 8: Verifying setup..."
if [ -f "tests/verify_setup.py" ]; then
    uv run python3 tests/verify_setup.py
else
    echo "✓ Setup complete. You can now run: uv run pytest tests/"
fi