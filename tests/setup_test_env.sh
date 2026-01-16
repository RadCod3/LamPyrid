#!/bin/bash
set -euo pipefail

echo "=== Automated Firefly III v6 Test Setup ==="
echo ""

# Step 1: Reset and start Firefly III
echo "Step 1: Starting Firefly III (with clean database)..."
docker-compose -f docker-compose.test.yml down -v --remove-orphans > /dev/null 2>&1 || true
docker-compose -f docker-compose.test.yml up -d

# Step 2: Wait for Firefly to be healthy
echo "Step 2: Waiting for Firefly III to initialize..."
MAX_RETRIES=30
RETRY_COUNT=0
HEALTH_URL="http://localhost:8080/health"

until $(curl --output /dev/null --silent --head --fail "$HEALTH_URL"); do
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
      echo -e "\n✗ Firefly III failed to start."
      docker-compose -f docker-compose.test.yml logs firefly-app | tail -n 20
      exit 1
    fi
    echo -n "."
    RETRY_COUNT=$((RETRY_COUNT+1))
    sleep 2
done

echo -e "\n✓ Health check passed. Finalizing database migrations..."
docker-compose -f docker-compose.test.yml exec -T firefly-app php artisan migrate --force > /dev/null 2>&1

# Step 3: Create User, User Group, and Link via Foreign Key
echo ""
echo "Step 3: Provisioning user and administration group..."

docker-compose -f docker-compose.test.yml exec -T firefly-app php -r "
    require 'vendor/autoload.php';
    \$app = require_once 'bootstrap/app.php';
    \$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
    
    try {
        \Illuminate\Support\Facades\DB::beginTransaction();

        // 1. Create or Find the User Group (Administration)
        // Firefly III v6 uses 'title' for the group name.
        \$group = \FireflyIII\Models\UserGroup::firstOrNew(['title' => 'Test Administration']);
        \$group->save();

        // 2. Create the User (Namespace: \FireflyIII based on your provided file)
        \$user = \FireflyIII\User::firstOrNew(['email' => 'test@lampyrid.local']);
        \$user->password = \Illuminate\Support\Facades\Hash::make('secret_password_123');
        
        // 3. Set the Administration ID directly (mapped to 'user_group_id' in your source)
        \$user->user_group_id = \$group->id;
        \$user->save();

        \Illuminate\Support\Facades\DB::commit();
        echo '✓ User test@lampyrid.local created and linked to Group #' . \$group->id . PHP_EOL;
    } catch (\Exception \$e) {
        \Illuminate\Support\Facades\DB::rollBack();
        fwrite(STDERR, '✗ Provisioning Error: ' . \$e->getMessage() . PHP_EOL);
        exit(1);
    }
"

# Step 4: Create personal access client
echo ""
echo "Step 4: Creating OAuth personal access client..."
docker-compose -f docker-compose.test.yml exec -T firefly-app \
    php artisan passport:client --personal --no-interaction --name="Test Client" > /dev/null 2>&1

# Step 5: Generate access token
echo ""
echo "Step 5: Generating API access token..."
TOKEN=$(docker-compose -f docker-compose.test.yml exec -T firefly-app php -r "
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

# Step 7: Test data will be created programmatically by tests
echo ""
echo "Step 7: Test setup complete!"
echo "  → Tests will create accounts and budgets programmatically"

# Step 8: Verify
echo ""
echo "Step 8: Verifying setup..."
if [ -f "tests/verify_setup.py" ]; then
    uv run python3 tests/verify_setup.py
else
    echo "✓ Setup complete. You can now run: uv run pytest tests/"
fi