{
  description = "Dev env for Zen/Firefox browser plugin + Python Discord RPC relay";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        name = "zen-discord-rpc-env";

        buildInputs = [
          # JS / Browser extension
          pkgs.nodejs_22
          pkgs.nodePackages.npm
          pkgs.nodePackages.web-ext

          # Other
          pkgs.zip

          # Python + libs for RPC server
          (pkgs.python3.withPackages (ps: with ps; [
            pypresence
            requests
            websockets
          ]))
        ];
      };

      nixosConfigurations.prez = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [
          ({ config, pkgs, ... }: {
            networking.hostName = "prez";
          })
        ];
      };
    };
}
