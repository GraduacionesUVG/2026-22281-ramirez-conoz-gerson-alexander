from pathlib import Path
import runpy
import tempfile
import unittest


MODULE = runpy.run_path(str(Path(__file__).parents[1] / "scripts/ci-context.py"))


def configuration():
    return {
        "AWS_ACCOUNT_ID": "111111111111",
        "AWS_DEPLOY_ROLE_ARN": "arn:aws:iam::111111111111:role/congenia-111111-gha-deploy",
        "AWS_REGION": "us-east-1",
        "TF_STATE_BUCKET": "congenia-tfstate-111111111111",
        "TF_NAME_PREFIX": "congenia-111111",
        "TF_DOMAIN_NAME": "cogenia.app",
    }


class ContextTests(unittest.TestCase):
    def test_cross_account_role_is_rejected_before_files_are_written(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = configuration() | {"AWS_DEPLOY_ROLE_ARN": "arn:aws:iam::222222222222:role/old", "RUNNER_TEMP": str(root / "temp"), "GITHUB_ENV": str(root / "env")}
            with self.assertRaisesRegex(ValueError, "pertenecer"):
                MODULE["prepare"](values)
            self.assertEqual(list(root.iterdir()), [])

    def test_required_values_and_environment_injection_are_rejected(self):
        for name in configuration():
            values = configuration()
            values.pop(name)
            with self.subTest(missing=name), self.assertRaisesRegex(ValueError, name):
                MODULE["settings"](values)
        for name, value in {"TF_DOMAIN_NAME": "cogenia.app\nAWS_PROFILE=other", "TF_NAME_PREFIX": "old;apply", "TF_STATE_BUCKET": "bucket\nregion=other", "AWS_REGION": "us-east-1\nother"}.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                MODULE["settings"](configuration() | {name: value})

    def test_backend_and_runtime_context_stay_on_the_selected_account(self):
        with tempfile.TemporaryDirectory(prefix="ci context ") as directory:
            root = Path(directory)
            environment = root / "env"
            environment.write_text("PREVIOUS=value\n")
            exports = MODULE["prepare"](configuration() | {"RUNNER_TEMP": directory, "GITHUB_ENV": str(environment)})
            backend = root / "congenia-backend.hcl"
            self.assertIn('allowed_account_ids = ["111111111111"]', backend.read_text())
            self.assertIn('bucket = "congenia-tfstate-111111111111"', backend.read_text())
            self.assertEqual(backend.stat().st_mode & 0o777, 0o600)
            self.assertEqual(exports["TF_VAR_name_prefix"], "congenia-111111")
            self.assertEqual(exports["TF_VAR_domain_name"], "cogenia.app")
            self.assertIn("-backend-config='", exports["TF_CLI_ARGS_init"])
            self.assertTrue(environment.read_text().startswith("PREVIOUS=value\n"))
            self.assertNotIn("222222222222", environment.read_text())


if __name__ == "__main__":
    unittest.main()
