{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs { inherit system; };

      buildPackage = python: pythonPackages:
        let
          buildPythonPackage = pythonPackages.buildPythonPackage;

          propagatedBuildInputs = with pythonPackages; [
            beautifulsoup4
            setuptools
          ];

        in

        buildPythonPackage {
          inherit propagatedBuildInputs;

          pname = "ogp";
          version = "0.9.1";

          src = ./.;

          doCheck = false;

          meta = with pkgs.lib; {
            description = "A module to parse the Open Graph Protocol";
            license = licenses.mit;
            platforms = platforms.all;
          };
        };


      mkShell = python: pythonPackages:
        pkgs.mkShell {
          packages = with pkgs; [
            python
            zlib
          ];

          propagatedBuildInputs = with pythonPackages; [
            beautifulsoup4
          ];


          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.zlib
            pkgs.stdenv.cc.cc
          ];
        };

    in
    with pkgs; {
      devShells.default = mkShell python311 python311Packages;
      packages.python311Packages.ogp = buildPackage python311 python311Packages;
      packages.python312Packages.ogp = buildPackage python312 python312Packages;
    });
}
