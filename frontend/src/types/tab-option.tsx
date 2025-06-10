enum TabOption {
  PLANNER = "planner",
  BROWSER = "browser",
  JUPYTER = "jupyter",
  VSCODE = "vscode",
  NOVNC = "novnc",
}

type TabType =
  | TabOption.PLANNER
  | TabOption.BROWSER
  | TabOption.JUPYTER
  | TabOption.VSCODE
  | TabOption.NOVNC;

const AllTabs = [
  TabOption.VSCODE,
  TabOption.BROWSER,
  TabOption.PLANNER,
  TabOption.JUPYTER,
  TabOption.NOVNC,
];

export { AllTabs, TabOption, type TabType };
