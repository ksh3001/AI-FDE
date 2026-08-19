import { useEffect, useState, type ReactNode } from "react";
import { Header } from "./components/Header";
import { Home } from "./components/Home";
import { Journey } from "./components/Journey";
import { PromptLibrary } from "./components/PromptLibrary";
import { SiteFooter } from "./components/SiteFooter";
import { UploadScreen } from "./components/UploadScreen";
import { Workspace } from "./components/Workspace";

type Route =
  | { view: "home" }
  | { view: "journey" }
  | { view: "generator" }
  | { view: "library" }
  | { view: "run"; runId: string };

function parseRoute(hash: string): Route {
  const runMatch = hash.match(/^#\/runs\/([^/]+)$/);
  if (runMatch) return { view: "run", runId: runMatch[1] };
  if (hash === "#/journey") return { view: "journey" };
  if (hash === "#/generator") return { view: "generator" };
  if (hash === "#/library") return { view: "library" };
  return { view: "home" };
}

/** Shared chrome for every page except the run workspace, which owns the full
 * viewport for its own dense working UI (stage rail, artifact pane, action bar). */
function SiteShell({ fillHeight, children }: { fillHeight?: boolean; children: ReactNode }) {
  return (
    <div className={fillHeight ? "flex h-screen flex-col" : "flex min-h-screen flex-col"}>
      <Header />
      <div className={fillHeight ? "min-h-0 flex-1" : "flex-1"}>{children}</div>
      {!fillHeight && <SiteFooter />}
    </div>
  );
}

export default function App() {
  const [route, setRoute] = useState<Route>(() => parseRoute(window.location.hash));

  useEffect(() => {
    const onHashChange = () => setRoute(parseRoute(window.location.hash));
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  switch (route.view) {
    case "run":
      return (
        <Workspace
          runId={route.runId}
          onBack={() => {
            window.location.hash = "#/";
          }}
        />
      );
    case "journey":
      return (
        <SiteShell fillHeight>
          <Journey />
        </SiteShell>
      );
    case "generator":
      return (
        <SiteShell>
          <UploadScreen
            onRunCreated={(id) => {
              window.location.hash = `#/runs/${id}`;
            }}
          />
        </SiteShell>
      );
    case "library":
      return (
        <SiteShell>
          <PromptLibrary />
        </SiteShell>
      );
    case "home":
      return (
        <SiteShell>
          <Home
            onOpenJourney={() => {
              window.location.hash = "#/journey";
            }}
            onOpenGenerator={() => {
              window.location.hash = "#/generator";
            }}
            onOpenLibrary={() => {
              window.location.hash = "#/library";
            }}
          />
        </SiteShell>
      );
  }
}
