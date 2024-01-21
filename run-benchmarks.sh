source benchmark-settings.config

# Create setup for hello benchmark

cd benchmark/hello
docker build -t spade_hello .
docker compose up -d
cd ../..

# Create setup for messaging benchmark

cd benchmark/messaging
docker build -t spade_messaging .
docker compose up -d
cd ../..

# Create setup for contract net protocol benchmark

cd benchmark/contract-net-protocol
docker build -t spade_cnp .
docker compose up -d
cd ../..