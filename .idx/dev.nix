# To learn more about how to use Nix to configure your environment
# see: https://developers.google.com/idx/guides/customize-idx-env
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.flutter
    pkgs.android-sdk
    pkgs.nodePackages.firebase-tools
    pkgs.jdk17
    pkgs.unzip
  ];

  # Sets environment variables in the workspace
  env = {
    ANDROID_HOME = "${pkgs.android-sdk}/share/android-sdk";
  };
  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      "Dart-Code.flutter"
      "Dart-Code.dart-code"
    ];

    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        # Build Flutter web / SDKs
        build-flutter = "cd samsun_mobil_app && flutter pub get";
      };
    };

    # Enable previews
    previews = {
      enable = true;
      previews = {
        web = {
          # Example: run "flutter run --machine -d web-server"
          command = ["flutter" "run" "--machine" "-d" "web-server" "--web-hostname" "0.0.0.0" "--web-port" "$PORT"];
          manager = "flutter";
          cwd = "samsun_mobil_app";
        };
        android = {
          # Example: run "flutter run --machine -d android"
          command = ["flutter" "run" "--machine" "-d" "android" "-d" "localhost:5555"];
          manager = "flutter";
          cwd = "samsun_mobil_app";
        };
      };
    };
  };
}
