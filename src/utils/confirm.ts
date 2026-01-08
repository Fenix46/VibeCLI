import inquirer from "inquirer";

export async function confirm(message: string, defaultValue = false): Promise<boolean> {
  const answer = (await inquirer.prompt([
    {
      type: "confirm",
      name: "ok",
      message,
      default: defaultValue
    }
  ])) as { ok: boolean };
  return Boolean(answer.ok);
}
