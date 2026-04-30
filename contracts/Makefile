.PHONY: install build test deploy fmt clean

LIB_DIR := lib

install:
	@mkdir -p $(LIB_DIR)
	@if [ ! -d "$(LIB_DIR)/forge-std" ]; then \
		git clone --depth 1 https://github.com/foundry-rs/forge-std $(LIB_DIR)/forge-std; \
	fi
	@if [ ! -d "$(LIB_DIR)/openzeppelin-contracts" ]; then \
		git clone --depth 1 https://github.com/OpenZeppelin/openzeppelin-contracts $(LIB_DIR)/openzeppelin-contracts; \
	fi

build: install
	forge build

test: install
	forge test -vvv

deploy: install
	forge script script/Deploy.s.sol:DeploySpieon \
		--rpc-url base_sepolia \
		--private-key $$AGENT_PRIVATE_KEY \
		--broadcast --verify

fmt:
	forge fmt

clean:
	rm -rf cache out broadcast
